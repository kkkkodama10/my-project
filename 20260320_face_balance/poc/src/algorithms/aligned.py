"""Exp-A: 顔アライメント（目の水平補正）後に Baseline 特徴量を抽出。"""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).parent.parent))
from detector import get_detector
from .base import FaceEmbedder
from .baseline import extract_features

_L_EYE = 33
_R_EYE = 263


def _align(image_bytes: bytes) -> bytes | None:
    """目の水平線が揃うよう画像を回転補正する。"""
    result = get_detector().detect(image_bytes)
    if result.face_count != 1:
        return None

    lm = result.landmarks
    l_eye = lm[_L_EYE, :2]
    r_eye = lm[_R_EYE, :2]

    pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    img = np.array(pil, dtype=np.uint8)
    h, w = img.shape[:2]

    dy = float((r_eye[1] - l_eye[1]) * h)
    dx = float((r_eye[0] - l_eye[0]) * w)
    angle = float(np.degrees(np.arctan2(dy, dx)))

    cx = int((l_eye[0] + r_eye[0]) / 2 * w)
    cy = int((l_eye[1] + r_eye[1]) / 2 * h)

    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    aligned = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR)

    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(aligned, cv2.COLOR_RGB2BGR))
    return bytes(buf) if ok else None


class AlignedEmbedder(FaceEmbedder):
    name = "aligned"

    def embed(self, image_path: str) -> np.ndarray | None:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        aligned_bytes = _align(image_bytes)
        if aligned_bytes is None:
            return None

        result = get_detector().detect(aligned_bytes)
        return extract_features(result)
