import unittest

import numpy as np

from scanner_app.core.scanner import compare_images


class CompareImagesTests(unittest.TestCase):
    def test_identical_frames_are_ok(self):
        master = np.zeros((120, 160, 3), dtype=np.uint8)

        result = compare_images(master, master.copy())

        self.assertEqual(result.status, "OK")
        self.assertEqual(result.difference_count, 0)

    def test_large_change_is_ng_and_highlighted(self):
        master = np.zeros((120, 160, 3), dtype=np.uint8)
        inspection = master.copy()
        inspection[30:80, 45:105] = 255

        result = compare_images(master, inspection, sensitivity=20, min_area=100)

        self.assertEqual(result.status, "NG")
        self.assertEqual(result.difference_count, 1)
        self.assertGreater(result.changed_area, 0)
        self.assertFalse(np.array_equal(result.annotated_frame, inspection))

    def test_different_frame_sizes_are_compared(self):
        master = np.zeros((120, 160, 3), dtype=np.uint8)
        inspection = np.zeros((60, 80, 3), dtype=np.uint8)

        result = compare_images(master, inspection)

        self.assertEqual(result.status, "OK")
        self.assertEqual(result.annotated_frame.shape, master.shape)


if __name__ == "__main__":
    unittest.main()
