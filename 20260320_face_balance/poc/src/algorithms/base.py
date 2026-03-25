"""全アルゴリズム共通の基底クラスと類似度計算ユーティリティ。"""
from abc import ABC, abstractmethod

import numpy as np


class FaceEmbedder(ABC):
    """顔画像 → 特徴量ベクトルの変換インターフェース。

    各実験（Baseline, Exp-A, Exp-E ...）はこのクラスを継承して実装する。
    """

    name: str  # 実験名（results/ のサブディレクトリ名に使用）

    @abstractmethod
    def embed(self, image_path: str) -> np.ndarray | None:
        """画像パスから特徴量ベクトルを返す。

        顔が検出できない場合は None を返す。
        """
        ...


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """コサイン類似度（0.0〜1.0）を返す。"""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def euclidean_similarity(a: np.ndarray, b: np.ndarray, scale: float = 1.0) -> float:
    """ユークリッド距離を類似度（0〜1）に変換して返す。scale で調整。"""
    dist = float(np.linalg.norm(a - b))
    return float(np.exp(-dist / scale))
