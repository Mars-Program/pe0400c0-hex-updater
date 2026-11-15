import copy,hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('validator',Path(__file__).parents[1]/'scripts/validate_site.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)

class PublicationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        files={'.nojekyll':'','index.html':'<meta http-equiv="refresh" content="0;url=./versions/0.1.5/">',
               'versions/0.1.5/index.html':'<title>fixture</title>','versions/0.1.5/app.js':'// fixture',
               'versions/0.1.5/_framework/dotnet.js':'// fixture runtime'}
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
        manifest={'version':'0.1.5','files':entries}
        raw=json.dumps(manifest).encode();(self.root/'SHA256SUMS.json').write_bytes(raw)
        record={'version':'0.1.5','sourceCommit':'a'*40,'localZipSha256':'B'*64,'siteManifestSha256':hashlib.sha256(raw).hexdigest(),'validation':dict.fromkeys(['BUILD','OFFLINE'],'PASS')|dict.fromkeys(['TRANSPORT','HARDWARE','HMI','POWER_LOSS','macOSExecution'],'NOT_RUN')}
        (self.root/'releases/current.json').write_text(json.dumps(record))
        return entries

    def test_verified_artifact_is_accepted(self):
        self.assertEqual(validator.validate(self.root)[2]['result'],'PASS')

    def test_modified_payload_rejected(self):
        (self.root/'versions/0.1.5/app.js').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):validator.validate(self.root)

    def test_traversal_rejected_even_with_declared_hash(self):
        entries=self.refresh();entries.append({'path':'../secret','bytes':0,'sha256':'0'*64});self.refresh(entries)
        with self.assertRaisesRegex(ValueError,'Unsafe manifest'):validator.validate(self.root)

    def test_duplicate_entry_rejected(self):
        entries=self.refresh();entries.append(copy.deepcopy(entries[0]));self.refresh(entries)
        with self.assertRaisesRegex(ValueError,'Duplicate'):validator.validate(self.root)

    def test_unlisted_qa_file_rejected(self):
        (self.root/'versions/0.1.5/qa.js').write_text('private QA')
        with self.assertRaisesRegex(ValueError,'Unmanifested'):validator.validate(self.root)

    def test_manifested_qa_file_rejected(self):
        (self.root/'versions/0.1.5/qa.js').write_text('private QA');self.refresh()
        with self.assertRaisesRegex(ValueError,'Unexpected public'):validator.validate(self.root)

    def test_old_version_cannot_be_rehashed_to_hide_mutation(self):
        def git(*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.DEVNULL,text=True).strip()
        git('init','-b','main');git('config','core.autocrlf','false');git('config','user.name','Offline test');git('config','user.email','test@example.invalid')
        git('add','.');git('commit','-m','fixture baseline');baseline=git('rev-parse','HEAD')
        (self.root/'versions/0.1.5/app.js').write_text('changed but rehashed');self.refresh()
        with self.assertRaisesRegex(ValueError,'Previous version mutated'):validator.validate(self.root,baseline)

if __name__=='__main__':unittest.main()
