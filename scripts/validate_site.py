"""Validate an immutable publication and optionally materialize its exact Pages artifact."""
from pathlib import Path,PurePosixPath
import argparse,gzip,hashlib,json,os,re,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preview_contract import verify_release

ROOT_ASSETS={'index.html','app.js','channel.js','journal.js','preferences.js','site-context.js','style.css'}
VERSION=re.compile(r'(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})\Z')

def require(condition,message):
    if not condition:raise ValueError(message)

def allowed(name):
    if name in {'.nojekyll','index.html','README.md','notices/DotNet-LICENSE.TXT','notices/DotNet-THIRD-PARTY-NOTICES.TXT'}:return True
    parts=PurePosixPath(name).parts
    if len(parts)<3 or parts[0]!='versions' or not VERSION.fullmatch(parts[1]):return False
    plain='/'.join(parts[2:])
    if plain.endswith(('.gz','.br')):plain=plain.rsplit('.',1)[0]
    return plain in ROOT_ASSETS or (plain.startswith('_framework/') and len(PurePosixPath(plain).parts)==2 and PurePosixPath(plain).suffix in {'.js','.json','.wasm'})

def validate(root,base_ref=None):
    root=Path(root).resolve()
    raw=(root/'SHA256SUMS.json').read_bytes(); manifest=json.loads(raw)
    version=manifest.get('version',''); match=VERSION.fullmatch(version)
    require(match is not None and all(int(n)<=255 for n in match.groups()),'Invalid canonical version')
    release=json.loads((root/'releases/current.json').read_text(encoding='utf-8-sig'))
    digest=hashlib.sha256(raw).hexdigest().upper()
    require(release['version']==version,'Release and manifest version differ')
    require(release['siteManifestSha256'].upper()==digest,'Release manifest identity differs')
    require(re.fullmatch(r'[0-9a-f]{40}',release['sourceCommit']) is not None,'Exact source commit required')
    require(re.fullmatch(r'[0-9A-Fa-f]{64}',release['localZipSha256']) is not None,'Exact local ZIP identity required')
    for name in ['BUILD','OFFLINE','TRANSPORT','HARDWARE','HMI','POWER_LOSS','macOSExecution']:
        require(release['validation'].get(name) in ['PASS','PARTIAL','NOT_RUN','FAIL'],'Missing evidence dimension: '+name)
    require(release['validation']['BUILD']=='PASS' and release['validation']['OFFLINE']=='PASS','Build and offline evidence required')
    require(os.environ.get('EXPECTED_VERSION',version)==version,'Requested release version differs')
    require(os.environ.get('EXPECTED_MANIFEST_SHA256',digest).upper()==digest,'Requested manifest hash differs')
    entries={}
    for item in manifest['files']:
        name=item['path']; p=PurePosixPath(name)
        require(not p.is_absolute() and '\\' not in name and '..' not in p.parts and str(p)==name,'Unsafe manifest path')
        require(allowed(name),'Unexpected public asset: '+name)
        require(name not in entries,'Duplicate manifest entry: '+name)
        path=root/name
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),'Missing or unsafe asset: '+name)
        data=path.read_bytes()
        require(len(data)==item['bytes'] and hashlib.sha256(data).hexdigest().upper()==item['sha256'].upper(),'Asset hash mismatch: '+name)
        if name.endswith('.gz'):require(gzip.decompress(data)==(root/name[:-3]).read_bytes(),'Compressed asset differs: '+name)
        if not name.endswith(('.gz','.br')):
            for marker in [b'C:\\TouchGFXProjects',b'C:/TouchGFXProjects',b'C:\\Users\\user',b'-----BEGIN PRIVATE KEY-----']:
                require(marker not in data,'Private data in asset: '+name)
            require(not re.search(rb'(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}',data),'Credential-like asset data')
        entries[name]=item
    actual={p.relative_to(root).as_posix() for folder in ['versions','notices'] for p in (root/folder).rglob('*') if p.is_file()}
    require(actual=={n for n in entries if n.startswith(('versions/','notices/'))},'Unmanifested or missing deployment asset')
    for n in ['index.html','.nojekyll',f'versions/{version}/index.html',f'versions/{version}/app.js',f'versions/{version}/_framework/dotnet.js']:
        require(n in entries,'Required deployment asset absent: '+n)
    require(f'url=./versions/{version}/' in (root/'index.html').read_text(),'Stable route does not select the release')
    if base_ref and set(base_ref)!={'0'}:
        require(re.fullmatch('[0-9a-f]{40}',base_ref) is not None,'Base must be an exact Git commit')
        tree=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-z',base_ref,'--','versions'])
        old={}
        for line in tree.split(b'\0'):
            if not line:continue
            info,name=line.split(b'\t',1); mode,kind,identity=info.split()
            require(kind==b'blob' and mode==b'100644','Unsafe previous version entry')
            old[name.decode()]=identity.decode()
        old_versions={PurePosixPath(n).parts[1] for n in old}
        for n,identity in old.items():
            require(n in entries,'Previous version removed: '+n)
            data=(root/n).read_bytes()
            require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==identity,'Previous version mutated: '+n)
        require(all(n in old or PurePosixPath(n).parts[1] not in old_versions for n in entries if n.startswith('versions/')),'File added to an immutable version')
    preview=verify_release(root,release,entries)
    return manifest,entries,{'result':'PASS','version':version,'siteManifestSha256':digest,'sourceCommit':release['sourceCommit'],'files':len(entries)+1,**preview}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--base-ref');parser.add_argument('--out')
    args=parser.parse_args();root=Path(args.root).resolve()
    _,entries,report=validate(root,args.base_ref)
    if args.out:
        destination=Path(args.out).resolve();require(not destination.exists(),'Refusing to overwrite a Pages artifact')
        for name in [*entries,'SHA256SUMS.json']:
            output=destination/name;output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,output)
    print(json.dumps(report))

if __name__=='__main__':main()
