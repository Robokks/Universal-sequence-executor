import json
import tempfile
import unittest
from pathlib import Path
from lvbatch import core
from lvbatch.mcp_client import success, _equal, _extract_value


class BatchContractTests(unittest.TestCase):
    def test_batch_count_and_first_batch(self):
        obj = core.load_batches()
        self.assertEqual(obj['application_vi_count'], 124)
        self.assertEqual(obj['utility_vi_count'], 28)
        self.assertEqual(len(core.get_batch('U01')['vi_names']), 6)

    def test_catalog_unique_variants(self):
        for pane in ('4815', '4833'):
            self.assertEqual(len(core.load_catalog(pane=pane)), 28)

    def test_intent_embeds_requirements(self):
        row = core.load_catalog()['UE_Relative_Target']
        text = core.vi_intent(row, 'Relative servo displacement')
        self.assertIn('SRS-F-020', text)
        self.assertIn('reference_mm', text)
        self.assertIn('hitch', text)
        self.assertIn('INTENT', text)

    def test_no_duplicate_test_ids(self):
        tests = core.get_tests()
        self.assertEqual(len(tests), 66)
        self.assertEqual(len(tests), len({t['Test ID'] for t in tests}))

    def test_baseline_well_formed(self):
        p = core.project_root()
        for pane in ('4815', '4833'):
            for name, entry in core.load_catalog(pane=pane).items():
                file = p / 'baseline' / entry['path']
                self.assertTrue(core.check_aixml(file, name + '.vi')['ok'], file.name)

    def test_prepared_batch_is_documented(self):
        data = core.prepare_batch('U01')
        self.assertEqual(len(data['items']), 6)
        self.assertTrue(all(Path(row['xml']).is_file() for row in data['items']))
        for row in data['items']:
            from xml.etree import ElementTree as ET
            desc = ET.parse(row['xml']).getroot().get('description')
            self.assertIn('INTENT:', desc)
            self.assertIn('REQUIREMENTS:', desc)
            self.assertTrue((core.project_root()/'outputs/U01/vi_docs'/f'{Path(row["name"]).stem}.md').is_file())

    def test_offline_lint_rejects_bad_nets(self):
        with tempfile.TemporaryDirectory() as tmp:
            test = Path(tmp)/'bad.xml'
            test.write_text('<VI _name="bad.vi" description="x"><Indicator uid="1" value="0" '
                            'inputs="value:does.not.exist"/></VI>', encoding='utf8')
            self.assertFalse(core.check_aixml(test)['ok'])

    def test_mcp_missing_result_never_passes(self):
        self.assertFalse(success({}))
        self.assertFalse(success({'errorCode':1}))
        self.assertTrue(success({'ok':True}))
        self.assertFalse(_equal(None, 0))
        self.assertTrue(_equal(2.0, 2))
        self.assertFalse(_equal(True, 1))
        self.assertIsNone(_extract_value({},'foo'))


if __name__ == '__main__':
    unittest.main()
