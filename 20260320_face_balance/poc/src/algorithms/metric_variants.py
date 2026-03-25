"""Exp-C: 類似度指標の変更

Baseline の15次元特徴量に対して異なる類似度指標を試す:
- euclidean: ユークリッド距離 → exp(-d) で類似度化
- manhattan: マンハッタン距離 → exp(-d) で類似度化
- correlation: ピアソン相関係数
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cityblock

sys.path.insert(0, str(Path(__file__).parent.parent))
from .base import FaceEmbedder
from .baseline import BaselineEmbedder


class _MetricVariantEmbedder(FaceEmbedder):
    """Baseline 埋め込みをそのまま使い、evaluate 側で類似度を差し替えるためのラッパー。

    similarity_fn を持ち、evaluate.py 側で呼び出す。
    """

    def __init__(self):
        self._base = BaselineEmbedder()

    def embed(self, image_path: str) -> np.ndarray | None:
        return self._base.embed(image_path)

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        raise NotImplementedError


class EuclideanEmbedder(_MetricVariantEmbedder):
    name = "euclidean"

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dist = float(np.linalg.norm(a - b))
        return float(np.exp(-dist * 5.0))  # scale factor to spread scores


class ManhattanEmbedder(_MetricVariantEmbedder):
    name = "manhattan"

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dist = float(cityblock(a, b))
        return float(np.exp(-dist * 3.0))


class CorrelationEmbedder(_MetricVariantEmbedder):
    name = "correlation"

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if np.std(a) < 1e-9 or np.std(b) < 1e-9:
            return 0.0
        corr = float(np.corrcoef(a, b)[0, 1])
        return (corr + 1.0) / 2.0  # [-1, 1] → [0, 1]
