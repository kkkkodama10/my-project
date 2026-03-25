"""Exp-D: スコア正規化（z-score 変換）

Baseline の特徴量を z-score 正規化してからコサイン類似度を取る。
全画像の特徴量を先に計算し、次元ごとに平均0・分散1に変換する。
→ スコアのダイナミックレンジが広がり、識別力が向上する可能性がある。
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from .base import FaceEmbedder
from .baseline import BaselineEmbedder


class NormalizedEmbedder(FaceEmbedder):
    """2パス方式: 1パス目で全画像の統計量を計算、2パス目で正規化済み埋め込みを返す。

    evaluate.py から使う場合、calibrate() を先に呼ぶ必要がある。
    calibrate() を呼ばない場合は生の特徴量をそのまま返す。
    """
    name = "normalized"

    def __init__(self):
        self._base = BaselineEmbedder()
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._cache: dict[str, np.ndarray] = {}

    def calibrate(self, image_paths: list[str]) -> None:
        """全画像の特徴量を計算し、正規化パラメータを設定する。"""
        embeddings = []
        for path in image_paths:
            emb = self._base.embed(path)
            if emb is not None:
                embeddings.append(emb)
                self._cache[path] = emb

        if not embeddings:
            return

        matrix = np.stack(embeddings)
        self._mean = matrix.mean(axis=0)
        self._std = matrix.std(axis=0)
        self._std[self._std < 1e-9] = 1.0  # ゼロ除算防止

    def embed(self, image_path: str) -> np.ndarray | None:
        if image_path in self._cache:
            raw = self._cache[image_path]
        else:
            raw = self._base.embed(image_path)
            if raw is None:
                return None

        if self._mean is not None:
            return (raw - self._mean) / self._std
        return raw
