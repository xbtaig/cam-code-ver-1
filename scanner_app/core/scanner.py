from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class InspectionResult:
    status: str
    annotated_frame: np.ndarray
    difference_count: int
    changed_area: int


def compare_images(master, inspection, sensitivity=35, min_area=150):
    """Compare two fixed-camera images and highlight changed image regions."""
    if master is None or inspection is None:
        raise ValueError("Both a master image and an inspection image are required.")

    height, width = master.shape[:2]
    if inspection.shape[:2] != (height, width):
        inspection = cv2.resize(inspection, (width, height), interpolation=cv2.INTER_AREA)

    master_gray = cv2.cvtColor(master, cv2.COLOR_BGR2GRAY)
    inspection_gray = cv2.cvtColor(inspection, cv2.COLOR_BGR2GRAY)
    master_gray = cv2.GaussianBlur(master_gray, (5, 5), 0)
    inspection_gray = cv2.GaussianBlur(inspection_gray, (5, 5), 0)

    difference = cv2.absdiff(master_gray, inspection_gray)
    _, mask = cv2.threshold(difference, int(sensitivity), 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = [
        contour for contour in contours
        if cv2.contourArea(contour) >= int(min_area)
    ]

    annotated = inspection.copy()
    overlay = annotated.copy()
    if regions:
        cv2.drawContours(overlay, regions, -1, (0, 0, 255), thickness=cv2.FILLED)
        annotated = cv2.addWeighted(overlay, 0.28, annotated, 0.72, 0)
        cv2.drawContours(annotated, regions, -1, (0, 0, 255), thickness=2)
        for contour in regions:
            x, y, box_width, box_height = cv2.boundingRect(contour)
            cv2.rectangle(
                annotated,
                (x, y),
                (x + box_width, y + box_height),
                (0, 0, 255),
                2,
            )

    changed_area = int(sum(cv2.contourArea(contour) for contour in regions))
    return InspectionResult(
        status="NG" if regions else "OK",
        annotated_frame=annotated,
        difference_count=len(regions),
        changed_area=changed_area,
    )
