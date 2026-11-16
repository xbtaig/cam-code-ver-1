import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from scanner_app.core.scanner import InspectionResult
from scanner_app.core.storage import InspectionStorage


class InspectionStorageTests(unittest.TestCase):
    def test_master_and_inspection_are_saved_under_data_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory) / "data"
            storage = InspectionStorage(data_dir=data_dir)
            image = np.zeros((32, 48, 3), dtype=np.uint8)

            storage.save_master(image)
            saved_master = storage.load_master()
            saved_capture = storage.save_capture(image)
            result = InspectionResult("OK", image, 0, 0)
            saved_result = storage.save_inspection(result)

            self.assertTrue(storage.master_path.is_relative_to(data_dir))
            self.assertEqual(saved_master.shape, image.shape)
            self.assertTrue(saved_capture.is_relative_to(data_dir / "captures"))
            self.assertEqual(cv2.imread(str(saved_capture)).shape, image.shape)
            self.assertTrue(saved_result.is_relative_to(data_dir / "results"))
            self.assertTrue(storage.log_path.is_file())
            self.assertIn("timestamp,status", storage.log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
