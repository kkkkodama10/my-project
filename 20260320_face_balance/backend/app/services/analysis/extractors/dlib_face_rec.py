"""dlib ベースの 128次元顔埋め込み抽出器。

face_recognition ライブラリを使用し、学習済み ResNet モデルで
128次元の顔埋め込みベクトルを生成する。
"""
import io
import logging
import threading

import numpy as np
from PIL import Image as PILImage

from app.services.analysis.detectors.base import LandmarkResult

logger = logging.getLogger(__name__)

try:
    import face_recognition
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False
    logger.warning(
        "face_recognition is not installed. DlibFaceRecExtractor is unavailable."
    )


class DlibFaceRecExtractor:
    """dlib 128次元顔埋め込み抽出器。

    face_recognition.face_encodings() で 128次元ベクトルを生成する。
    スレッドセーフ。
    """

    model_version: str = "dlib_face_rec_v1"

    def __init__(self) -> None:
        if not _AVAILABLE:
            raise ImportError(
                "face_recognition がインストールされていません。"
                "requirements.txt を確認してください。"
            )
        self._lock = threading.Lock()

    def extract(self, result: LandmarkResult) -> list[float]:
        """LandmarkResult からの抽出（未使用だが Protocol 互換のため定義）。"""
        raise NotImplementedError(
            "DlibFaceRecExtractor は extract_from_image() を使用してください"
        )

    def extract_from_image(self, image_bytes: bytes) -> list[float] | None:
        """画像バイト列から 128次元埋め込みベクトルを返す。

        顔が検出できない場合は None を返す。
        """
        pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(pil)

        with self._lock:
            encodings = face_recognition.face_encodings(img_array)

        if not encodings:
            return None

        return encodings[0].tolist()
