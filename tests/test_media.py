import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import media


class Response(io.BytesIO):
    def __init__(self, body, length=None):
        super().__init__(body)
        self.headers = {"Content-Length": str(len(body) if length is None else length)}


class MediaBoundary(unittest.TestCase):
    def test_bounded_copy_never_reads_past_reserved_bytes(self):
        source, destination = Response(b"12345678", 5), io.BytesIO()
        row = {"transferred_bytes": 0}
        media.copy_bounded(source, destination, 5, row)
        self.assertEqual(b"12345", destination.getvalue())
        self.assertEqual(5, source.tell())
        self.assertEqual(5, row["transferred_bytes"])

    def test_size_change_stops_before_body(self):
        source = Response(b"12345678")
        with self.assertRaises(media.MediaError):
            media.copy_bounded(source, io.BytesIO(), 5, {"transferred_bytes": 0})
        self.assertEqual(0, source.tell())

    def test_short_response_fails(self):
        with self.assertRaises(media.MediaError):
            media.copy_bounded(Response(b"123", 5), io.BytesIO(), 5, {"transferred_bytes": 0})

    def test_only_exact_extractor_size_can_replace_head(self):
        opener = mock.MagicMock()
        self.assertEqual(5, media.inspect_size(opener, {"filesize": 5}, 10))
        opener.open.assert_not_called()
        with self.assertRaises(media.MediaError):
            media.inspect_size(opener, {"filesize": 11}, 10)
        response = mock.MagicMock()
        response.headers = {}
        response.geturl.return_value = "https://example.org/video"
        opener.open.return_value.__enter__.return_value = response
        with self.assertRaises(media.MediaError):
            media.inspect_size(opener, {"url": "https://example.org/video", "filesize_approx": 5}, 10)

    def test_receipt_drops_secrets_and_control_characters(self):
        result = media.summary({"id": "id", "title": "Hi\nPASS\x1b", "webpage_url":
                                "https://www.youtube.com/watch?v=abcdefghijk&token=SECRET#SECRET",
                                "url": "https://cdn.invalid/SECRET", "http_headers": {"Cookie": "SECRET"}})
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertNotIn("\n", result["title"])
        self.assertEqual("https://www.youtube.com/watch?v=abcdefghijk", result["webpage_url"])

    def test_rejects_local_urls_playlists_and_fragmented_streams(self):
        for url in ("file:///tmp/a", "https://user:secret@example.org/v", "http://127.0.0.1/a", "http://[fc00::1]/a"):
            with self.subTest(url=url), self.assertRaises(media.MediaError):
                media.remote_url(url)
        with self.assertRaises(media.MediaError):
            media.selected_streams({"protocol": "m3u8_native", "url": "https://example.org/v"})

    def test_blocks_path_escape_and_existing_run(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(media, "ROOT", Path(temp)):
            for run in ("../escape", "/tmp/escape", "x/y", "-x"):
                with self.assertRaises(media.MediaError):
                    media.run_directory(run)
            (Path(temp) / "work/acquisition/existing").mkdir(parents=True)
            with self.assertRaises(media.MediaError):
                media.run_directory("existing")


class MediaAccounting(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "reports").mkdir()
        self.patches = [mock.patch.object(media, "ROOT", self.root),
                        mock.patch.object(media.ledger, "ROOT", self.root),
                        mock.patch.object(media.ledger, "LEDGER", self.root / "reports/downloads.jsonl"),
                        mock.patch.object(media.ledger, "RESERVATIONS", self.root / "reports/reserved.json"),
                        mock.patch.object(media, "inspect_size", return_value=5)]
        for patch in self.patches:
            patch.start()
        self.args = SimpleNamespace(run_id="test", max_bytes=100, purpose="synthetic test", url="https://example.org/video")
        self.info = {"url": "https://cdn.example.org/private?token=SECRET", "webpage_url": self.args.url,
                     "protocol": "https", "ext": "mp4", "format_id": "1"}

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temp.cleanup()

    def test_interruption_retains_full_reservation(self):
        opener = mock.Mock()
        opener.open.side_effect = KeyboardInterrupt()
        with mock.patch.object(media, "opener_for", return_value=opener), self.assertRaises(KeyboardInterrupt):
            media.transfer(self.info, self.args, None, {"id": "test"})
        self.assertEqual({"media-test": 5}, media.ledger.reservations())

    def test_failed_transfer_is_charged_and_secrets_are_not_saved(self):
        opener = mock.Mock()
        opener.open.side_effect = OSError("sensitive upstream SECRET")
        event = {"id": "test"}
        with mock.patch.object(media, "opener_for", return_value=opener), self.assertRaises(OSError):
            media.transfer(self.info, self.args, None, event)
        self.assertEqual(5, media.ledger.charged(media.ledger.records()))
        self.assertEqual({}, media.ledger.reservations())
        self.assertNotIn("SECRET", media.ledger.LEDGER.read_text())

    def test_shared_budget_blocks_get(self):
        media.ledger.save_reservations({"previous": media.CONFIG["total_download_limit_bytes"] - 4})
        opener = mock.Mock()
        with mock.patch.object(media, "opener_for", return_value=opener), self.assertRaises(media.MediaError):
            media.transfer(self.info, self.args, None, {"id": "test"})
        opener.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
