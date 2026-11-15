"""Prepare an accepted hosted candidate for a production PR; never commit or deploy."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path

import preview_contract as contract
from validate_site import validate


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def prepare(root, candidate, expected_sha, approval_reference, fetcher=contract.fetch):
    root = Path(root).resolve()
    require = contract.require
    require(bool(approval_reference.strip()), 'Explicit candidate acceptance reference required')
    validate(root)
    url = contract.candidate_url(candidate)
    raw = fetcher(url + 'candidate.json')
    record, files = contract.parse_record(raw, candidate, expected_sha)
    version = record['version']
    destination = root / 'versions' / version
    require(not destination.exists(), 'Production version is immutable; choose a new version')
    require(not (root / 'releases' / (version + '.json')).exists()
            and not (root / 'releases' / (version + '-preview.json')).exists(), 'Release record already exists')
    def download(item):
        name, expected = item
        data = fetcher(url + name, expected['bytes'])
        require(len(data) == expected['bytes'] and contract.digest(data) == expected['sha256'].upper(),
                'Hosted preview asset hash mismatch: ' + name)
        return name, data
    with ThreadPoolExecutor(max_workers=6) as pool:
        payload = dict(pool.map(download, files.items()))
    # All remote content is verified before the first write to this checkout.
    for name, data in payload.items():
        path = destination / name[4:] if name.startswith('app/') else root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (root / 'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta http-equiv="refresh" content="0;url=./versions/{version}/">'
        '<meta name="robots" content="noindex,nofollow"><title>HEX Updater</title></head>'
        f'<body><a href="./versions/{version}/">Open HEX Updater {version}</a></body></html>\n', encoding='utf-8')
    paths = [root / n for n in ['.nojekyll', 'index.html', 'README.md']]
    paths += [p for name in ['versions', 'notices'] for p in (root / name).rglob('*') if p.is_file()]
    entries = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
                'sha256': contract.digest(p.read_bytes())} for p in sorted(paths)]
    manifest = encoded({'tool': 'PE0400C0 HEX Updater Web', 'version': version, 'files': entries})
    release = {k: record[k] for k in ['version', 'sourceRepository', 'sourceCommit', 'sourceTree',
                                      'localZipName', 'localZipSha256', 'validation']}
    release.update({'schema': 1, 'kind': 'ACCEPTED_PREVIEW',
                    'siteManifestSha256': contract.digest(manifest),
                    'preview': {'candidateId': candidate, 'url': url, 'manifestUrl': url + 'candidate.json',
                                'manifestSha256': contract.digest(raw)},
                    'approval': {'reference': approval_reference,
                                 'recordedAt': datetime.now(timezone.utc).isoformat(timespec='seconds')}})
    (root / 'SHA256SUMS.json').write_bytes(manifest)
    (root / 'releases' / (version + '-preview.json')).write_bytes(raw)
    (root / 'releases' / (version + '.json')).write_bytes(encoded(release))
    (root / 'releases/current.json').write_bytes(encoded(release))
    report = validate(root)[2]
    report.update({'preparedOnly': True, 'productionDeployed': False, 'preview': candidate})
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--verify', action='store_true', help='Read-only hosted preview check for the current release')
    parser.add_argument('--candidate')
    parser.add_argument('--record-sha256')
    parser.add_argument('--approval-reference')
    args = parser.parse_args()
    if args.verify:
        _, entries, report = validate(args.root)
        release = json.loads((Path(args.root) / 'releases/current.json').read_bytes())
        report.update(contract.verify_release(args.root, release, entries, online=True))
    else:
        if not all([args.candidate, args.record_sha256, args.approval_reference]):
            parser.error('--candidate, --record-sha256 and --approval-reference are required')
        report = prepare(args.root, args.candidate, args.record_sha256, args.approval_reference)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
