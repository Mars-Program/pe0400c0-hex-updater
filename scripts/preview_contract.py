"""Require future production bytes to match an explicitly accepted hosted preview."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import urllib.request

PREVIEW = 'https://mars-program.github.io/pe0400c0-hex-updater-preview/candidates/'
SOURCE = 'Mars-Program/pe0400c0-hex-updater-source'
BASELINE_MANIFEST = '5D4705E9BD37B8EA2B685035CC45311657EA174C08A64B089353625F0112B176'
BASELINE_SOURCE = 'd303c7d663c4d315d748df3f953c812c1e8d5bf1'
BASELINE_ZIP = '297ECD60B1D842AEAC96C5C68B383AAD4306F8F73AAAE7BCA2E3995B72BEFCBB'
ASSETS = {'index.html', 'app.js', 'channel.js', 'journal.js', 'preferences.js', 'site-context.js', 'style.css'}
NOTICES = {'notices/DotNet-LICENSE.TXT', 'notices/DotNet-THIRD-PARTY-NOTICES.TXT'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def candidate_url(candidate):
    require(bool(re.fullmatch(r'(?:0|[1-9][0-9]{0,2})\.(?:0|[1-9][0-9]{0,2})\.(?:0|[1-9][0-9]{0,2})-[0-9]{8}-[0-9]{3}', candidate)), 'Invalid preview candidate ID')
    return PREVIEW + candidate + '/'


def fetch(url, limit=2 * 1024 * 1024):
    require(url.startswith(PREVIEW), 'Network request outside preview site')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    request = urllib.request.Request(url, headers={'User-Agent': 'HexUpdater-Preview-Promotion'})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=40) as response:
        require(response.status == 200 and response.geturl() == url, 'Unexpected preview response')
        data = response.read(limit + 1)
    require(len(data) <= limit, 'Preview response too large')
    return data


def parse_record(raw, candidate, expected_sha):
    require(bool(re.fullmatch('[0-9a-fA-F]{64}', expected_sha)), 'Exact preview manifest SHA256 required')
    require(digest(raw) == expected_sha.upper(), 'Preview manifest hash differs')
    record = json.loads(raw)
    require(record['schema'] == 1 and record['channel'] == 'preview', 'Invalid preview schema')
    require(record['candidateId'] == candidate and candidate.startswith(record['version'] + '-'), 'Preview version/candidate differs')
    candidate_url(candidate)
    require(all(int(n) <= 255 for n in record['version'].split('.')), 'Invalid preview version')
    require(record['sourceRepository'] == SOURCE, 'Wrong preview source repository')
    for field in ['sourceCommit', 'sourceTree']:
        require(bool(re.fullmatch('[0-9a-f]{40}', record[field])), 'Invalid preview source identity')
    require(bool(re.fullmatch('[0-9a-fA-F]{64}', record['localZipSha256'])), 'Invalid preview ZIP hash')
    require(bool(re.fullmatch(r'[A-Za-z0-9_.-]+\.zip', record['localZipName'])), 'Invalid preview ZIP filename')
    files = {}
    for item in record['files']:
        name = item['path']
        p = PurePosixPath(name)
        require(not p.is_absolute() and '\\' not in name and ':' not in name and '..' not in p.parts and str(p) == name, 'Unsafe preview asset path')
        plain = name[4:] if name.startswith('app/') else ''
        if plain.endswith(('.gz', '.br')):
            plain = plain.rsplit('.', 1)[0]
        parts = PurePosixPath(plain).parts
        allowed = name in NOTICES or (name.startswith('app/') and (
            plain in ASSETS or (len(parts) == 2 and parts[0] == '_framework'
                                and PurePosixPath(plain).suffix in {'.js', '.json', '.wasm'})))
        require(allowed and name.casefold() not in {n.casefold() for n in files}, 'Unexpected or duplicate preview asset')
        require(type(item['bytes']) is int and 0 <= item['bytes'] <= 64 * 1024 * 1024, 'Invalid preview asset size')
        require(bool(re.fullmatch('[0-9a-fA-F]{64}', item['sha256'])), 'Invalid preview asset hash')
        files[name] = item
    require({'app/index.html', 'app/app.js', 'app/_framework/dotnet.js'} | NOTICES <= set(files), 'Preview runtime/notices missing')
    require(sum(x['bytes'] for x in files.values()) <= 512 * 1024 * 1024, 'Candidate exceeds size limit')
    for gate in ['BUILD', 'OFFLINE', 'TRANSPORT', 'HARDWARE', 'HMI', 'POWER_LOSS', 'macOSExecution']:
        require(record['validation'].get(gate) in ['PASS', 'PARTIAL', 'NOT_RUN', 'FAIL'], 'Invalid preview evidence')
    require(all(record['validation'][g] == 'PASS' for g in ['BUILD', 'OFFLINE']), 'Preview build/offline checks required')
    return record, files


def baseline(release):
    return (release['version'] == '0.1.5'
            and release.get('kind') == 'EXISTING_ENGINEERING_PREVIEW'
            and release['sourceCommit'] == BASELINE_SOURCE
            and release['localZipSha256'].upper() == BASELINE_ZIP
            and release['siteManifestSha256'].upper() == BASELINE_MANIFEST)


def verify_release(root, release, site_entries, online=False):
    if baseline(release) and 'preview' not in release:
        return {'preview': 'EXISTING_IMMUTABLE_0.1.5_BASELINE'}
    require(isinstance(release.get('preview'), dict), 'New release requires an accepted preview')
    preview = release['preview']
    require(isinstance(release.get('approval'), dict)
            and bool(release['approval'].get('reference', '').strip()), 'Explicit candidate acceptance reference required')
    url = candidate_url(preview['candidateId'])
    require(preview['url'] == url and preview['manifestUrl'] == url + 'candidate.json', 'Preview URL differs')
    raw = (Path(root) / 'releases' / (release['version'] + '-preview.json')).read_bytes()
    record, files = parse_record(raw, preview['candidateId'], preview['manifestSha256'])
    for field in ['version', 'sourceRepository', 'sourceCommit', 'sourceTree', 'localZipName', 'localZipSha256']:
        require(record[field] == release[field], 'Release differs from accepted preview: ' + field)
    require(record['validation'] == release['validation'], 'Preview evidence cannot be silently upgraded')
    mapped = {}
    for name, item in files.items():
        destination = 'versions/' + record['version'] + '/' + name[4:] if name.startswith('app/') else name
        mapped[destination] = item
        require(destination in site_entries, 'Preview asset absent from production')
        actual = site_entries[destination]
        require(actual['bytes'] == item['bytes'] and actual['sha256'].upper() == item['sha256'].upper(), 'Production bytes differ from accepted preview')
    require({n for n in site_entries if n.startswith('versions/' + record['version'] + '/')}
            == {n for n in mapped if n.startswith('versions/')}, 'Extra production runtime outside preview')
    if online:
        require(fetch(preview['manifestUrl']) == raw, 'Hosted preview differs from accepted record')
    return {'preview': preview['candidateId'], 'previewManifestSha256': digest(raw), 'hostedPreviewChecked': online}
