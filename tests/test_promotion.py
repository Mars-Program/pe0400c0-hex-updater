import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import preview_contract
import promote_preview
import test_publication


class PromotionChecks(unittest.TestCase):
    def setUp(self):
        self.fixture = test_publication.PublicationChecks()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.record = json.loads((self.root / 'releases/0.1.6-preview.json').read_bytes())
        self.record.update({'version': '0.1.7', 'candidateId': '0.1.7-20261116-001'})
        self.raw = json.dumps(self.record).encode()
        self.hash = hashlib.sha256(self.raw).hexdigest()
        self.url = preview_contract.candidate_url(self.record['candidateId'])
        self.payload = {}
        for item in self.record['files']:
            path = 'versions/0.1.6/' + item['path'][4:] if item['path'].startswith('app/') else item['path']
            self.payload[self.url + item['path']] = (self.root / path).read_bytes()
        self.payload[self.url + 'candidate.json'] = self.raw

    def fetch(self, url, limit=None):
        return self.payload[url]

    def test_prepare_copies_identical_bytes_and_keeps_old_version(self):
        old = (self.root / 'versions/0.1.6/app.js').read_bytes()
        result = promote_preview.prepare(self.root, self.record['candidateId'], self.hash,
                                         'Synthetic unit-test acceptance only', self.fetch)
        self.assertTrue(result['preparedOnly'])
        self.assertFalse(result['productionDeployed'])
        self.assertEqual((self.root / 'versions/0.1.7/app.js').read_bytes(), old)
        self.assertEqual((self.root / 'versions/0.1.6/app.js').read_bytes(), old)
        self.assertEqual((self.root / 'releases/0.1.7-preview.json').read_bytes(), self.raw)
        self.assertFalse((self.root / 'versions/0.1.7/candidate.json').exists())

    def test_tampered_download_does_not_modify_publication(self):
        before = (self.root / 'SHA256SUMS.json').read_bytes()
        self.payload[self.url + 'app/app.js'] = b'tampered'
        with self.assertRaisesRegex(ValueError, 'Hosted preview asset hash mismatch'):
            promote_preview.prepare(self.root, self.record['candidateId'], self.hash,
                                    'Synthetic unit-test acceptance only', self.fetch)
        self.assertEqual((self.root / 'SHA256SUMS.json').read_bytes(), before)
        self.assertFalse((self.root / 'versions/0.1.7').exists())

    def test_existing_version_cannot_be_overwritten(self):
        raw = (self.root / 'releases/0.1.6-preview.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Production version is immutable'):
            promote_preview.prepare(self.root, '0.1.6-20261116-001', hashlib.sha256(raw).hexdigest(),
                                    'Synthetic unit-test acceptance only', lambda *args: raw)

    def test_no_acceptance_no_fetch_or_write(self):
        def forbidden(*args):
            self.fail('Fetch must not occur without acceptance')
        with self.assertRaisesRegex(ValueError, 'acceptance reference'):
            promote_preview.prepare(self.root, self.record['candidateId'], self.hash, '', forbidden)

    def test_outside_preview_url_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid preview candidate ID'):
            preview_contract.candidate_url('../production')


if __name__ == '__main__':
    unittest.main()
