import math

import numpy as np

from app.services.analysis.detectors.base import LandmarkResult

# MediaPipe Face Mesh ランドマークインデックス
_L_EYE_OUTER = 33    # 左目外角（IPD基準L）
_R_EYE_OUTER = 263   # 右目外角（IPD基準R）
_NOSE_TIP = 4        # 鼻先
_NOSE_ROOT = 168     # 鼻根
_NOSE_BASE = 2       # 鼻下
_MOUTH_L = 61        # 口左角
_MOUTH_R = 291       # 口右角
_CHEEK_L = 234       # 左頬
_CHEEK_R = 454       # 右頬
_FOREHEAD = 10       # 額
_CHIN = 152          # 顎
_BROW_L_INNER = 55   # 左眉内端
_BROW_R_INNER = 285  # 右眉内端
_BROW_L_OUTER = 105  # 左眉外端


def _pt(landmarks: np.ndarray, idx: int) -> np.ndarray:
    """landmarks から 2D 座標 (x, y) を取得する。"""
    return landmarks[idx, :2]


def _dist2d(a: np.ndarray, b: np.ndarray) -> float:
    """2D ユークリッド距離。"""
    return float(np.linalg.norm(a - b))


def _angle_deg(p1: np.ndarray, vertex: np.ndarray, p2: np.ndarray) -> float:
    """3点の角度（度）を返す。vertex が頂点。"""
    v1 = p1 - vertex
    v2 = p2 - vertex
    cos_val = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    cos_val = float(np.clip(cos_val, -1.0, 1.0))
    return math.degrees(math.acos(cos_val))


class DistanceRatioExtractor:
    """IPD 正規化距離比率ベクトルを算出する特徴量抽出器（15次元）。"""

    model_version: str = "mediapipe_v0.10_distance_ratio_v1"

    def extract(self, result: LandmarkResult) -> list[float]:
        lm = result.landmarks  # shape: (468, 3)

        # 基準: IPD（瞳孔間距離）
        l_eye = _pt(lm, _L_EYE_OUTER)
        r_eye = _pt(lm, _R_EYE_OUTER)
        ipd = _dist2d(l_eye, r_eye)
        if ipd < 1e-9:
            return [0.0] * 15

        nose_tip = _pt(lm, _NOSE_TIP)
        nose_root = _pt(lm, _NOSE_ROOT)
        nose_base = _pt(lm, _NOSE_BASE)
        mouth_l = _pt(lm, _MOUTH_L)
        mouth_r = _pt(lm, _MOUTH_R)
        cheek_l = _pt(lm, _CHEEK_L)
        cheek_r = _pt(lm, _CHEEK_R)
        forehead = _pt(lm, _FOREHEAD)
        chin = _pt(lm, _CHIN)
        brow_l_inner = _pt(lm, _BROW_L_INNER)
        brow_r_inner = _pt(lm, _BROW_R_INNER)
        brow_l_outer = _pt(lm, _BROW_L_OUTER)

        # ===== 距離特徴量 5次元 ÷ IPD =====
        nose_length = _dist2d(nose_root, nose_tip) / ipd          # 鼻長
        mouth_width = _dist2d(mouth_l, mouth_r) / ipd             # 口幅
        face_width = _dist2d(cheek_l, cheek_r) / ipd             # 顔幅
        brow_gap = _dist2d(brow_l_inner, brow_r_inner) / ipd     # 眉間距離
        eye_mouth_v = _dist2d(
            (l_eye + r_eye) / 2, (mouth_l + mouth_r) / 2
        ) / ipd                                                    # 目口垂直距離

        # ===== 角度特徴量 3次元（度）=====
        angle_eye_nose_eye = _angle_deg(l_eye, nose_tip, r_eye)
        angle_mouth_nose_mouth = _angle_deg(mouth_l, nose_tip, mouth_r)
        angle_brow_eye_nose = _angle_deg(brow_l_outer, l_eye, nose_root)

        # ===== 比率特徴量 7次元 =====
        face_height = _dist2d(forehead, chin)
        face_width_abs = _dist2d(cheek_l, cheek_r)
        eye_width_abs = _dist2d(l_eye, r_eye)                     # = IPD（目安）
        nose_length_abs = _dist2d(nose_root, nose_tip)
        mouth_width_abs = _dist2d(mouth_l, mouth_r)

        face_aspect_ratio = face_height / (face_width_abs + 1e-9)  # 顔縦横比
        eye_face_ratio = eye_width_abs / (face_width_abs + 1e-9)   # 目幅/顔幅
        nose_face_ratio = nose_length_abs / (face_height + 1e-9)   # 鼻長/顔高
        mouth_ipd_ratio = mouth_width_abs / (ipd + 1e-9)           # 口幅/IPD

        # 三分割比（上：額-鼻根、中：鼻根-鼻下、下：鼻下-顎）
        upper = _dist2d(forehead, nose_root)
        middle = _dist2d(nose_root, nose_base)
        lower = _dist2d(nose_base, chin)
        total_thirds = upper + middle + lower + 1e-9
        ratio_upper = upper / total_thirds
        ratio_middle = middle / total_thirds
        ratio_lower = lower / total_thirds

        return [
            # 距離 (5)
            nose_length,
            mouth_width,
            face_width,
            brow_gap,
            eye_mouth_v,
            # 角度 (3)
            angle_eye_nose_eye,
            angle_mouth_nose_mouth,
            angle_brow_eye_nose,
            # 比率 (7)
            face_aspect_ratio,
            eye_face_ratio,
            nose_face_ratio,
            mouth_ipd_ratio,
            ratio_upper,
            ratio_middle,
            ratio_lower,
        ]
