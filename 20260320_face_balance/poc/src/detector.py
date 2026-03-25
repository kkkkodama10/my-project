"""
MediaPipe Tasks API (0.10.14+) を使ったスタンドアロン顔ランドマーク検出器。

旧 mp.solutions.face_mesh は 0.10.14 以降で削除されたため、
PoC では Tasks API を使用する。

モデルファイル: poc/face_landmarker.task
  （ダウンロード済みであること）
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image as PILImage
import io

MODEL_PATH = Path(__file__).parent.parent / "face_landmarker.task"

_BaseOptions = mp.tasks.BaseOptions
_FaceLandmarker = mp.tasks.vision.FaceLandmarker
_FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
_RunningMode = mp.tasks.vision.RunningMode


@dataclass
class LandmarkResult:
    """468点ランドマーク座標（正規化済み 0-1）と顔検出数。

    旧 API の LandmarkResult と同一インターフェース。
    """
    landmarks: np.ndarray  # shape: (468, 3) — x, y, z
    face_count: int


class TasksLandmarkDetector:
    """Tasks API ベースの顔ランドマーク検出器（スレッドセーフ）。

    FaceLandmarker は create/close を繰り返すのが重いため、
    インスタンス単位でコンテキストマネージャとして使う。
    """

    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"モデルファイルが見つかりません: {MODEL_PATH}\n"
                "以下を実行してダウンロードしてください:\n"
                "  curl -L -o poc/face_landmarker.task \\\n"
                '    "https://storage.googleapis.com/mediapipe-models/'
                'face_landmarker/face_landmarker/float16/1/face_landmarker.task"'
            )
        options = _FaceLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=_RunningMode.IMAGE,
            num_faces=2,
            min_face_detection_confidence=0.5,
        )
        self._detector = _FaceLandmarker.create_from_options(options)
        self._lock = threading.Lock()

    def detect(self, image_bytes: bytes) -> LandmarkResult:
        """画像バイト列から顔ランドマーク（468点）を検出する。"""
        # PIL → mediapipe.Image
        pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        np_img = np.array(pil, dtype=np.uint8)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np_img)

        with self._lock:
            result = self._detector.detect(mp_image)

        face_count = len(result.face_landmarks)

        if face_count == 0:
            return LandmarkResult(landmarks=np.empty((0, 3)), face_count=0)

        if face_count >= 2:
            return LandmarkResult(landmarks=np.empty((0, 3)), face_count=face_count)

        # 1顔のみ: 先頭 468点を (468, 3) に変換（虹彩の10点 468〜477 は除外）
        raw = result.face_landmarks[0]
        landmarks = np.array(
            [[lm.x, lm.y, lm.z] for lm in raw[:468]],
            dtype=np.float32,
        )
        return LandmarkResult(landmarks=landmarks, face_count=1)

    def close(self) -> None:
        self._detector.close()

    def __del__(self) -> None:
        try:
            self._detector.close()
        except Exception:
            pass


# シングルトン（モジュールロード時に1回だけ初期化）
_detector_instance: TasksLandmarkDetector | None = None
_init_lock = threading.Lock()


def get_detector() -> TasksLandmarkDetector:
    global _detector_instance
    if _detector_instance is None:
        with _init_lock:
            if _detector_instance is None:
                _detector_instance = TasksLandmarkDetector()
    return _detector_instance
