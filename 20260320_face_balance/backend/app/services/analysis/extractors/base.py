from typing import Protocol

import numpy as np

from app.services.analysis.detectors.base import LandmarkResult


class FeatureExtractor(Protocol):
    """特徴量抽出器インターフェース。"""

    model_version: str

    def extract(self, result: LandmarkResult) -> list[float]:
        """LandmarkResult から特徴量ベクトルを抽出して返す。"""
        ...

    def extract_from_image(self, image_bytes: bytes) -> list[float] | None:
        """画像バイト列から直接特徴量を抽出する。

        このメソッドが実装されている場合、pipeline は extract() より
        こちらを優先して呼び出す（hasattr チェックで分岐）。
        顔検出失敗時は None を返す。

        Protocol メンバーとして宣言。未実装のクラス（DistanceRatioExtractor 等）は
        このメソッドを持たないため、pipeline.py の hasattr() チェックで skip される。
        """
        ...
