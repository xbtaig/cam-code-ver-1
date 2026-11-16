import csv
from datetime import datetime
from pathlib import Path

import cv2


class InspectionStorage:
    """Keeps master samples and inspection records under the project data folder."""

    def __init__(self, data_dir=None):
        project_root = Path(__file__).resolve().parents[2]
        self.data_dir = Path(data_dir) if data_dir else project_root / "data"
        self.samples_dir = self.data_dir / "samples"
        self.captures_dir = self.data_dir / "captures"
        self.results_dir = self.data_dir / "results"
        self.master_path = self.samples_dir / "master.jpg"
        self.log_path = self.results_dir / "inspection_log.csv"
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def load_master(self):
        if not self.master_path.exists():
            return None
        image = cv2.imread(str(self.master_path))
        if image is None:
            raise OSError("The saved master sample could not be read.")
        return image

    def save_master(self, image):
        if not cv2.imwrite(str(self.master_path), image):
            raise OSError("Could not save the master sample image.")

    def save_capture(self, image):
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
        image_path = self.captures_dir / filename
        if not cv2.imwrite(str(image_path), image):
            raise OSError("Could not save the camera photo.")
        return image_path

    def save_inspection(self, result):
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + result.status + ".jpg"
        image_path = self.results_dir / filename
        if not cv2.imwrite(str(image_path), result.annotated_frame):
            raise OSError("Could not save the inspection image.")

        new_log = not self.log_path.exists()
        with self.log_path.open("a", newline="", encoding="utf-8") as log_file:
            writer = csv.writer(log_file)
            if new_log:
                writer.writerow(
                    ["timestamp", "status", "difference_regions", "changed_area_px", "image"]
                )
            writer.writerow(
                [
                    timestamp,
                    result.status,
                    result.difference_count,
                    result.changed_area,
                    filename,
                ]
            )
        return image_path
