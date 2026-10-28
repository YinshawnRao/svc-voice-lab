import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import separate


class ExperimentIsolation(unittest.TestCase):
    def test_explicit_files_exclude_earlier_artists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for role in ('target', 'source'):
                (root / 'data' / role).mkdir(parents=True)
                for name in ('old.wav', 'new.wav'):
                    (root / 'data' / role / name).touch()
            target, source = [root / 'data' / role / 'new.wav' for role in ('target', 'source')]
            with patch.object(separate, 'ROOT', root):
                self.assertEqual(separate.select_songs([target], [source]), [('target', target), ('source', source)])
                with self.assertRaises(ValueError):
                    separate.select_songs([target], None)
                with self.assertRaises(ValueError):
                    separate.select_songs([source], [source])
                escaped = root / 'data/target/escape.wav'
                escaped.symlink_to(source)
                with self.assertRaises(ValueError):
                    separate.select_songs([escaped], [source])


if __name__ == '__main__':
    unittest.main()
