import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from f0_repair import apply_f0_repair


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.f0 = [0., 466., 355., 350., 472., 0.]
        self.spec = {'schema_version': 1, 'source_sha256': 'expected', 'frame_seconds': .01,
                     'repairs': [{'start_frame': 2, 'end_frame_exclusive': 4,
                                  'expected_original_hz_range': [340, 365],
                                  'expected_anchor_hz_range': [460, 480]}]}

    def test_only_audited_frames_change(self):
        fixed, _ = apply_f0_repair(self.f0, self.spec, 'expected')
        self.assertEqual(fixed[:2], self.f0[:2])
        self.assertEqual(fixed[4:], self.f0[4:])
        self.assertEqual(self.f0[2:4], [355., 350.])
        self.assertTrue(466 < fixed[2] < fixed[3] < 472)

    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):
            apply_f0_repair(self.f0, self.spec, 'other-song')

    def test_unexpected_pitch_rejected(self):
        with self.assertRaises(ValueError):
            apply_f0_repair([0., 466., 0., 350., 472., 0.], self.spec, 'expected')


if __name__ == '__main__':
    unittest.main()
