import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from download import validate
import download
from slice_vocals import intervals

class DownloadBoundary(unittest.TestCase):
    def setUp(self):
        self.item = dict(url="https://huggingface.co/official/model/resolve/commit/file.pt", dest="models/file.pt",
                         size_bytes=1, license="unknown", evidence="https://github.com/official/repo", purpose="test",
                         kind="model", official_owner_verified=True)

    def test_refuses_budget_overflow_before_network(self):
        for changes, used in [({"size_bytes": 5000000001}, 0), ({"size_bytes": 2}, 29999999999), ({"size_bytes": None}, 0)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate({**self.item, **changes}, used)

    def test_refuses_remote_mirror_and_escape(self):
        for changes in [{"url": "http://huggingface.co/a"}, {"url": "https://hf-mirror.com/a"},
                        {"dest": "../outside.pt"}, {"dest": "data/target/model.pt"}, {"official_owner_verified": False}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate({**self.item, **changes}, 0)

    def test_exact_limits_are_allowed(self):
        validate({**self.item, "size_bytes": 5000000000}, 25000000000)

class SliceBoundary(unittest.TestCase):
    def test_all_silence_has_no_clips(self):
        self.assertEqual(intervals(10, "silence_start: 0\nsilence_end: 10"), ([], []))

    def test_trailing_silence_and_short_tail(self):
        clips, rejected = intervals(20, "silence_start: 16\nsilence_end: 20")
        self.assertEqual(clips, [(0.0, 15.0)])
        self.assertEqual(rejected[0]["start"], 15)

    def test_leading_silence_and_regions(self):
        clips, _ = intervals(12, "silence_start: 0\nsilence_end: 2\nsilence_start: 6\nsilence_end: 8")
        self.assertEqual(clips, [(2.0, 6.0), (8.0, 12)])

class DownloadExecution(unittest.TestCase):
    def run_in_temp(self, test):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "reports").mkdir()
            with patch.object(download, "ROOT", root), patch.object(download, "LEDGER", root / "reports/downloads.jsonl"), patch.object(download, "RESERVATIONS", root / "reports/reservations.json"):
                test(root)

    def test_oversize_never_opens_network(self):
        def scenario(root):
            item = dict(url="https://files.pythonhosted.org/test.whl", dest=".cache/test.whl", size_bytes=5000000001,
                        license="MIT", evidence="https://pypi.org/project/test", purpose="test", kind="dependency")
            with patch.object(download.urllib.request, "urlopen") as network, self.assertRaises(RuntimeError):
                download.download(item)
            network.assert_not_called()
            row = download.records()[0]
            self.assertEqual(row["status"], "SKIPPED")
            self.assertEqual(row["transferred_bytes"], 0)
        self.run_in_temp(scenario)

    def test_interruption_preserves_budget_reservation(self):
        def scenario(root):
            item = dict(url="https://files.pythonhosted.org/test.whl", dest=".cache/test.whl", size_bytes=3,
                        license="MIT", evidence="https://pypi.org/project/test", purpose="test", kind="dependency")
            with patch.object(download.urllib.request, "urlopen", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                download.download(item)
            self.assertEqual(sum(download.reservations().values()), 3)
        self.run_in_temp(scenario)

if __name__ == "__main__":
    unittest.main()
