import copy,hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('validator',Path(__file__).parents[1]/'scripts/validate_site.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)

class PublicationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        files={'.nojekyll':'','index.html':'<meta http-equiv="refresh" content="0;url=./versions/0.1.6/">',
               'versions/0.1.6/index.html':'<title>fixture</title>','versions/0.1.6/app.js':'// fixture',
               'versions/0.1.6/_framework/dotnet.js':'// fixture runtime',
               'notices/DotNet-LICENSE.TXT':'fixture notice',
               'notices/DotNet-THIRD-PARTY-NOTICES.TXT':'fixture notice',
               'README.md':'fixture publication'}
        for name,data in files.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data,encoding='utf-8')
        (self.root/'releases').mkdir()
        self.refresh()

    def refresh(self,entries=None):
        if entries is None:
            entries=[]
            for p in sorted(self.root.rglob('*')):
                if p.is_file() and (p.relative_to(self.root).parts[0] in ['versions','notices'] or p.name in ['.nojekyll','index.html']):
                    b=p.read_bytes();entries.append({'path':p.relative_to(self.root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
        manifest={'version':'0.1.6','files':entries}
        raw=json.dumps(manifest).encode();(self.root/'SHA256SUMS.json').write_bytes(raw)
        record={'version':'0.1.6','sourceCommit':'a'*40,'localZipSha256':'B'*64,'siteManifestSha256':hashlib.sha256(raw).hexdigest(),'validation':dict.fromkeys(['BUILD','OFFLINE'],'PASS')|dict.fromkeys(['TRANSPORT','HARDWARE','HMI','POWER_LOSS','macOSExecution'],'NOT_RUN')}
        record.update({'kind':'ACCEPTED_PREVIEW','sourceRepository':'Mars-Program/pe0400c0-hex-updater-source','sourceTree':'c'*40,'localZipName':'fixture.zip'})
        preview={k:record[k] for k in ['version','sourceRepository','sourceCommit','sourceTree','localZipName','localZipSha256','validation']}
        preview.update({'schema':1,'channel':'preview','candidateId':'0.1.6-20261116-001','summary':'fixture','files':[
            dict(x,path='app/'+x['path'].split('/',2)[2]) if x['path'].startswith('versions/') else x
            for x in entries if x['path'].startswith(('versions/','notices/'))]})
        preview_raw=json.dumps(preview).encode()
        (self.root/'releases/0.1.6-preview.json').write_bytes(preview_raw)
        url='https://mars-program.github.io/pe0400c0-hex-updater-preview/candidates/0.1.6-20261116-001/'
        record.update({'preview':{'candidateId':preview['candidateId'],'url':url,'manifestUrl':url+'candidate.json','manifestSha256':hashlib.sha256(preview_raw).hexdigest()},
                       'approval':{'reference':'Offline fixture acceptance only'}})
        (self.root/'releases/current.json').write_text(json.dumps(record))
        return entries

    def test_verified_artifact_is_accepted(self):
        self.assertEqual(validator.validate(self.root)[2]['result'],'PASS')

    def test_modified_payload_rejected(self):
        (self.root/'versions/0.1.6/app.js').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):validator.validate(self.root)

    def test_traversal_rejected_even_with_declared_hash(self):
        entries=self.refresh();entries.append({'path':'../secret','bytes':0,'sha256':'0'*64});self.refresh(entries)
        with self.assertRaisesRegex(ValueError,'Unsafe manifest'):validator.validate(self.root)

    def test_duplicate_entry_rejected(self):
        entries=self.refresh();entries.append(copy.deepcopy(entries[0]));self.refresh(entries)
        with self.assertRaisesRegex(ValueError,'Duplicate'):validator.validate(self.root)

    def test_unlisted_qa_file_rejected(self):
        (self.root/'versions/0.1.6/qa.js').write_text('private QA')
        with self.assertRaisesRegex(ValueError,'Unmanifested'):validator.validate(self.root)

    def test_manifested_qa_file_rejected(self):
        (self.root/'versions/0.1.6/qa.js').write_text('private QA');self.refresh()
        with self.assertRaisesRegex(ValueError,'Unexpected public'):validator.validate(self.root)

    def test_old_version_cannot_be_rehashed_to_hide_mutation(self):
        def git(*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.DEVNULL,text=True).strip()
        git('init','-b','main');git('config','core.autocrlf','false');git('config','user.name','Offline test');git('config','user.email','test@example.invalid')
        git('add','.');git('commit','-m','fixture baseline');baseline=git('rev-parse','HEAD')
        (self.root/'versions/0.1.6/app.js').write_text('changed but rehashed');self.refresh()
        with self.assertRaisesRegex(ValueError,'Previous version mutated'):validator.validate(self.root,baseline)

    def test_new_release_without_preview_rejected(self):
        p=self.root/'releases/current.json';record=json.loads(p.read_bytes());del record['preview'];p.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'requires an accepted preview'):validator.validate(self.root)

    def test_missing_candidate_acceptance_rejected(self):
        p=self.root/'releases/current.json';record=json.loads(p.read_bytes());record['approval']['reference']='';p.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'acceptance reference'):validator.validate(self.root)

    def test_preview_manifest_tampering_rejected(self):
        p=self.root/'releases/0.1.6-preview.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Preview manifest hash differs'):validator.validate(self.root)

    def test_preview_zip_binding_cannot_be_replaced(self):
        p=self.root/'releases/current.json';record=json.loads(p.read_bytes());record['localZipSha256']='C'*64;p.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'Release differs from accepted preview'):validator.validate(self.root)

    def test_rehashed_production_payload_must_still_match_preview(self):
        p=self.root/'versions/0.1.6/app.js';p.write_text('replacement')
        mpath=self.root/'SHA256SUMS.json';m=json.loads(mpath.read_bytes())
        for item in m['files']:
            if item['path']=='versions/0.1.6/app.js':item.update({'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        raw=json.dumps(m).encode();mpath.write_bytes(raw)
        rpath=self.root/'releases/current.json';r=json.loads(rpath.read_bytes());r['siteManifestSha256']=hashlib.sha256(raw).hexdigest();rpath.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,'Production bytes differ from accepted preview'):validator.validate(self.root)

if __name__=='__main__':unittest.main()
