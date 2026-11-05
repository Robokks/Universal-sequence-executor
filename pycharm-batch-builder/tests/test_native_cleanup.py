"""No LabVIEW required: cleanup refuses wrong paths, missing files, duplicates."""
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from lvbatch.native_cleanup import _targets


class NativeCleanupSafetyTests(TestCase):
    def test_only_known_scratch_batches_can_be_cleaned(self):
        with self.assertRaises(ValueError):
            _targets("A21")
        with self.assertRaises(ValueError):
            _targets("../../bad")

    def test_accepts_only_existing_scratch_vins(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            good = root / "outputs/U02/native/UE_Within_Tolerance.vi"
            good.parent.mkdir(parents=True)
            good.write_bytes(b"example bytes")
            with patch("lvbatch.native_cleanup.project_root", return_value=root), patch(
                    "lvbatch.native_cleanup.load_stage",
                    return_value={"items": [{"native_vi": str(good)}]}):
                self.assertEqual(_targets("U02"), [good.resolve()])

    def test_refuses_missing_outside_and_duplicate_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            correct = root / "outputs/U01/native/demo.vi"
            correct.parent.mkdir(parents=True)
            correct.write_bytes(b"example bytes")
            missing = correct.parent / "missing.vi"
            outside = root / "arbitrary.vi"
            outside.write_bytes(b"outside")
            for collection in ([missing], [outside], [correct, correct]):
                with patch("lvbatch.native_cleanup.project_root", return_value=root), patch(
                        "lvbatch.native_cleanup.load_stage",
                        return_value={"items": [{"native_vi": str(x)} for x in collection]}):
                    with self.assertRaises(ValueError):
                        _targets("U01")
