"""Exp-F: Landmark + LBP テクスチャ ハイブリッド

15次元ランドマーク特徴量 + 顔領域の LBP（局所二値パターン）ヒストグラムを結合。
骨格的な特徴 + 肌のきめ・テクスチャの両方を使うことで識別力向上を狙う。
"""
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


def _compute_lbp(gray: np.ndarray) -> np.ndarray:
    """簡易 LBP（8近傍）を計算し、ヒストグラム（256 bin）を返す。"""
    h, w = gray.shape
    lbp = np.zeros((h - 2, w - 2), dtype=np.uint8)

    # 8近傍: 時計回り
    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, 1),
               (1, 1), (1, 0), (1, -1), (0, -1)]

    for i, (dy, dx) in enumerate(offsets):
        neighbor = gray[1 + dy: h - 1 + dy, 1 + dx: w - 1 + dx]
        center = gray[1:h - 1, 1:w - 1]
        lbp |= ((neighbor >= center).astype(np.uint8) << i)

    hist, _ = np.histogram(lbp, bins=256, range=(0, 256))
    hist = hist.astype(np.float32)
    hist /= (hist.sum() + 1e-9)
    return hist


def _extract_face_region(image_bytes: bytes, landmarks: np.ndarray) -> np.ndarray | None:
    """ランドマークから顔領域を切り出し、グレースケール 128x128 で返す。"""
    pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    img = np.array(pil, dtype=np.uint8)
    h, w = img.shape[:2]

    # ランドマーク座標をピクセルに変換
    pts = landmarks[:, :2].copy()
    pts[:, 0] *= w
    pts[:, 1] *= h

    x_min = max(0, int(pts[:, 0].min()) - 10)
    x_max = min(w, int(pts[:, 0].max()) + 10)
    y_min = max(0, int(pts[:, 1].min()) - 10)
    y_max = min(h, int(pts[:, 1].max()) + 10)

    if x_max - x_min < 20 or y_max - y_min < 20:
        return None

    face_crop = img[y_min:y_max, x_min:x_max]
    gray = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, (128, 128))
    return resized


def _extract_grid_lbp(face_gray: np.ndarray, grid: int = 4) -> np.ndarray:
    """顔画像を grid x grid に分割し、各セルの LBP ヒストグラムを結合する。

    grid=4 → 16セル × 256bin = 4096次元 → PCA 不要、コサイン類似度で使える
    ただし次元が大きすぎるため、各セルを 32bin に量子化して 16×32=512次元にする。
    """
    h, w = face_gray.shape
    cell_h, cell_w = h // grid, w // grid
    histograms = []

    for gy in range(grid):
        for gx in range(grid):
            cell = face_gray[gy * cell_h:(gy + 1) * cell_h,
                             gx * cell_w:(gx + 1) * cell_w]
            lbp = _compute_lbp(cell)
            # 256bin → 32bin にダウンサンプル
            reduced = lbp.reshape(32, 8).sum(axis=1)
            reduced /= (reduced.sum() + 1e-9)
            histograms.append(reduced)

    return np.concatenate(histograms)


class HybridEmbedder(FaceEmbedder):
    name = "hybrid"

    def embed(self, image_path: str) -> np.ndarray | None:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        result = get_detector().detect(image_bytes)

        # ランドマーク特徴量 (15次元)
        landmark_feat = extract_features(result)
        if landmark_feat is None:
            return None

        # LBP テクスチャ特徴量 (512次元)
        face_gray = _extract_face_region(image_bytes, result.landmarks)
        if face_gray is None:
            return None

        lbp_feat = _extract_grid_lbp(face_gray, grid=4)

        # 結合時にランドマーク特徴量を重み付け（スケールを合わせる）
        # LBP は確率分布（合計≈1）、ランドマークは 0.x〜数十 のスケール
        # → ランドマーク特徴量を正規化してから結合
        lm_norm = landmark_feat / (np.linalg.norm(landmark_feat) + 1e-9)
        lbp_norm = lbp_feat / (np.linalg.norm(lbp_feat) + 1e-9)

        # 重み: ランドマーク 0.3 + LBP 0.7（テクスチャの方が情報量が多い）
        combined = np.concatenate([lm_norm * 0.3, lbp_norm * 0.7])
        return combined
