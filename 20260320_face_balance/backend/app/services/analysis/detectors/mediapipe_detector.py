import io
import threading

import mediapipe as mp
import numpy as np
from PIL import Image as PILImage

from app.services.analysis.detectors.base import LandmarkResult


class MediaPipeLandmarkDetector:
    """MediaPipe Face Mesh を使ったランドマーク検出器。

    BackgroundTasks から複数同時実行される可能性があるため、
    FaceMesh.process() 呼び出しを threading.Lock で保護する。
    """

    def __init__(self) -> None:
        # max_num_faces=2: 1枚を超えた顔を検出するために2に設定（3枚以上は2として返る）
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=2,
            refine_landmarks=False,
            min_detection_confidence=0.5,
        )
        self._lock = threading.Lock()

    def detect(self, image_bytes: bytes) -> LandmarkResult:
        pil_img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb_array = np.array(pil_img, dtype=np.uint8)

        with self._lock:
            results = self._face_mesh.process(rgb_array)

        if not results.multi_face_landmarks:
            return LandmarkResult(landmarks=np.empty((0, 3)), face_count=0)

        face_count = len(results.multi_face_landmarks)
        if face_count != 1:
            return LandmarkResult(landmarks=np.empty((0, 3)), face_count=face_count)

        face = results.multi_face_landmarks[0]
        landmarks = np.array(
            [[lm.x, lm.y, lm.z] for lm in face.landmark],
            dtype=np.float32,
        )
        return LandmarkResult(landmarks=landmarks, face_count=1)
