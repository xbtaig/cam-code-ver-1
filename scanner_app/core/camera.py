import threading
import time

import cv2


class Camera:
    """Reads webcam frames in the background so the UI stays responsive."""

    def __init__(self, camera_index=0):
        self._capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self._capture.isOpened():
            self._capture.release()
            raise RuntimeError(
                "Could not open the camera. Check that it is connected and not "
                "being used by another application."
            )

        self._lock = threading.Lock()
        self._frame = None
        self._error = None
        self._running = True
        self._thread = threading.Thread(target=self._read_frames, daemon=True)
        self._thread.start()

    def _read_frames(self):
        while self._running:
            success, frame = self._capture.read()
            if success:
                with self._lock:
                    self._frame = frame
                    self._error = None
            else:
                with self._lock:
                    self._error = "The camera stopped returning frames."
                time.sleep(0.1)

    def get_frame(self):
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def get_error(self):
        with self._lock:
            return self._error

    def close(self):
        self._running = False
        self._thread.join(timeout=1.0)
        self._capture.release()
