"""Exp-E: face_recognition ライブラリ（dlib 128次元埋め込み）

事前インストール:
    brew install cmake
    pip install face_recognition
"""
import numpy as np

from .base import FaceEmbedder

try:
    import face_recognition
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


class FaceRecEmbedder(FaceEmbedder):
    name = "face_rec"

    def __init__(self):
        if not _AVAILABLE:
            raise ImportError(
                "face_recognition がインストールされていません。\n"
                "  brew install cmake\n"
                "  pip install face_recognition"
            )

    def embed(self, image_path: str) -> np.ndarray | None:
        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            return None
        return np.array(encodings[0], dtype=np.float32)
