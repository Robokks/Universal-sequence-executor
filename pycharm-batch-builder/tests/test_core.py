import json
import tempfile
import unittest
from pathlib import Path
from lvbatch import core
from lvbatch.mcp_client import success, _equal, _extract_value
from lvbatch.layout import assign_connector, composer_pane_directive, native_subdir
from lvbatch.icon_catalog import icon_spec
import xml.etree.ElementTree as ET


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

    def test_connector_panes_put_inputs_left_and_outputs_right(self):
        catalog = core.load_catalog()
        samples = [
            ("UE_Ms_To_Seconds", 4801, [1], [0]),
            ("UE_Relative_Target", 4802, [2, 1], [0]),
            ("UE_Clamp_To_Limits", 4810, [5, 4, 3], [2, 1]),
            ("UE_Command_Permitted", 4815, [11, 10, 9, 8], [3]),
        ]
        for name, pattern_expected, left, right in samples:
            entry = catalog[name]
            root = ET.parse(core.project_root() / 'baseline' / entry['path']).getroot()
            pattern, mapping = assign_connector(root, entry, 'compact', '4815')
            self.assertEqual(pattern, pattern_expected)
            self.assertEqual([mapping[x['name']] for x in entry['inputs']], left)
            self.assertEqual([mapping[x['name']] for x in entry['outputs']], right)
            self.assertEqual(len(mapping), len(set(mapping.values())))

    def test_pane_directive_and_output_path_safety(self):
        self.assertIn('pane="4802"', composer_pane_directive(4802))
        self.assertEqual(native_subdir('native_refined'), 'native_refined')
        for wrong in ('../native', 'C:/native', '.git', 'outputs/nested'):
            with self.assertRaises(ValueError):
                native_subdir(wrong)

    def test_icon_lines_fit_labview_32px_limit(self):
        for name in core.load_catalog():
            value = icon_spec(name)
            self.assertEqual(value['line1'], 'UE')
            self.assertTrue(all(len(v) <= 5 for v in value.values()))

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
