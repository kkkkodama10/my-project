from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class LandmarkResult:
    """468点ランドマーク座標（正規化済み 0-1）と顔検出数。"""

    landmarks: np.ndarray  # shape: (468, 3) — x, y, z（正規化済み）
    face_count: int


class LandmarkDetector(Protocol):
    """ランドマーク検出器インターフェース。"""

    def detect(self, image_bytes: bytes) -> LandmarkResult:
        """画像バイト列から顔のランドマーク座標を検出する。

        face_count == 1 のとき landmarks に有効な座標が入る。
        face_count != 1 のとき landmarks は未定義（空配列など）。
        """
        ...
