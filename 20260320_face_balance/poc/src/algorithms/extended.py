"""Exp-B: ランドマーク次元拡張（15次元 → 45次元）

追加特徴量:
- 目の縦幅（左右）、鼻翼幅、唇の厚み、目頭間距離
- 左右対称性スコア
- 顎ライン角度
- 各パーツの相対位置ベクトル
"""
import io
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from detector import get_detector, LandmarkResult
from .base import FaceEmbedder

# --- ランドマークインデックス ---
# 基本（baseline と同一）
_L_EYE_OUTER  = 33
_R_EYE_OUTER  = 263
_NOSE_TIP     = 4
_NOSE_ROOT    = 168
_NOSE_BASE    = 2
_MOUTH_L      = 61
_MOUTH_R      = 291
_CHEEK_L      = 234
_CHEEK_R      = 454
_FOREHEAD     = 10
_CHIN         = 152
_BROW_L_INNER = 55
_BROW_R_INNER = 285
_BROW_L_OUTER = 105

# 追加
_L_EYE_INNER  = 133
_R_EYE_INNER  = 362
_L_EYE_TOP    = 159
_L_EYE_BTM    = 145
_R_EYE_TOP    = 386
_R_EYE_BTM    = 374
_NOSE_L_WING  = 129
_NOSE_R_WING  = 358
_UPPER_LIP    = 13
_LOWER_LIP    = 14
_MOUTH_TOP    = 0
_MOUTH_BTM    = 17
_BROW_R_OUTER = 334
_JAW_L        = 172
_JAW_R        = 397
_L_EAR        = 234
_R_EAR        = 454


def _pt(lm: np.ndarray, idx: int) -> np.ndarray:
    return lm[idx, :2]


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _angle_deg(p1: np.ndarray, vertex: np.ndarray, p2: np.ndarray) -> float:
    v1, v2 = p1 - vertex, p2 - vertex
    cos_val = float(np.clip(
        np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9),
        -1.0, 1.0,
    ))
    return math.degrees(math.acos(cos_val))


def extract_extended_features(result: LandmarkResult) -> np.ndarray | None:
    """LandmarkResult から 45次元特徴量ベクトルを返す。"""
    if result.face_count != 1:
        return None
    lm = result.landmarks

    l_eye = _pt(lm, _L_EYE_OUTER)
    r_eye = _pt(lm, _R_EYE_OUTER)
    ipd = _dist(l_eye, r_eye)
    if ipd < 1e-9:
        return None

    # 基本点
    l_eye_in  = _pt(lm, _L_EYE_INNER)
    r_eye_in  = _pt(lm, _R_EYE_INNER)
    l_eye_top = _pt(lm, _L_EYE_TOP)
    l_eye_btm = _pt(lm, _L_EYE_BTM)
    r_eye_top = _pt(lm, _R_EYE_TOP)
    r_eye_btm = _pt(lm, _R_EYE_BTM)
    nose_tip  = _pt(lm, _NOSE_TIP)
    nose_root = _pt(lm, _NOSE_ROOT)
    nose_base = _pt(lm, _NOSE_BASE)
    nose_l    = _pt(lm, _NOSE_L_WING)
    nose_r    = _pt(lm, _NOSE_R_WING)
    mouth_l   = _pt(lm, _MOUTH_L)
    mouth_r   = _pt(lm, _MOUTH_R)
    upper_lip = _pt(lm, _UPPER_LIP)
    lower_lip = _pt(lm, _LOWER_LIP)
    mouth_top = _pt(lm, _MOUTH_TOP)
    mouth_btm = _pt(lm, _MOUTH_BTM)
    cheek_l   = _pt(lm, _CHEEK_L)
    cheek_r   = _pt(lm, _CHEEK_R)
    forehead  = _pt(lm, _FOREHEAD)
    chin      = _pt(lm, _CHIN)
    brow_l_in = _pt(lm, _BROW_L_INNER)
    brow_r_in = _pt(lm, _BROW_R_INNER)
    brow_l_out = _pt(lm, _BROW_L_OUTER)
    brow_r_out = _pt(lm, _BROW_R_OUTER)
    jaw_l     = _pt(lm, _JAW_L)
    jaw_r     = _pt(lm, _JAW_R)

    eye_center = (l_eye + r_eye) / 2
    mouth_center = (mouth_l + mouth_r) / 2
    face_h = _dist(forehead, chin)
    face_w = _dist(cheek_l, cheek_r)

    features = []

    # === Baseline 15次元（再現） ===
    features.append(_dist(nose_root, nose_tip) / ipd)       # 鼻長
    features.append(_dist(mouth_l, mouth_r) / ipd)           # 口幅
    features.append(face_w / ipd)                             # 顔幅
    features.append(_dist(brow_l_in, brow_r_in) / ipd)       # 眉間
    features.append(_dist(eye_center, mouth_center) / ipd)    # 目-口 垂直距離

    features.append(_angle_deg(l_eye, nose_tip, r_eye))
    features.append(_angle_deg(mouth_l, nose_tip, mouth_r))
    features.append(_angle_deg(brow_l_out, l_eye, nose_root))

    features.append(face_h / (face_w + 1e-9))
    features.append(ipd / (face_w + 1e-9))
    features.append(_dist(nose_root, nose_tip) / (face_h + 1e-9))
    features.append(_dist(mouth_l, mouth_r) / (ipd + 1e-9))

    upper = _dist(forehead, nose_root)
    middle = _dist(nose_root, nose_base)
    lower = _dist(nose_base, chin)
    total = upper + middle + lower + 1e-9
    features.append(upper / total)
    features.append(middle / total)
    features.append(lower / total)

    # === 追加: 目の詳細 (6次元) ===
    l_eye_h = _dist(l_eye_top, l_eye_btm)
    r_eye_h = _dist(r_eye_top, r_eye_btm)
    l_eye_w = _dist(l_eye, l_eye_in)
    r_eye_w = _dist(r_eye_in, r_eye)
    features.append(l_eye_h / ipd)                  # 左目 縦幅
    features.append(r_eye_h / ipd)                  # 右目 縦幅
    features.append(l_eye_w / ipd)                  # 左目 横幅
    features.append(r_eye_w / ipd)                  # 右目 横幅
    features.append(l_eye_h / (l_eye_w + 1e-9))     # 左目 アスペクト比
    features.append(r_eye_h / (r_eye_w + 1e-9))     # 右目 アスペクト比

    # === 追加: 鼻の詳細 (4次元) ===
    nose_wing_w = _dist(nose_l, nose_r)
    features.append(nose_wing_w / ipd)              # 鼻翼幅
    features.append(nose_wing_w / (face_w + 1e-9))  # 鼻翼幅 / 顔幅
    features.append(_dist(nose_tip, nose_base) / ipd) # 鼻先-鼻底
    features.append(_angle_deg(nose_l, nose_tip, nose_r))  # 鼻翼角度

    # === 追加: 口・唇の詳細 (4次元) ===
    lip_h = _dist(upper_lip, lower_lip)
    mouth_h = _dist(mouth_top, mouth_btm)
    features.append(lip_h / ipd)                    # 唇の厚み
    features.append(mouth_h / ipd)                  # 口の縦幅
    features.append(lip_h / (_dist(mouth_l, mouth_r) + 1e-9))  # 唇アスペクト
    features.append(mouth_h / (face_h + 1e-9))      # 口 / 顔高さ

    # === 追加: 眉の詳細 (4次元) ===
    brow_l_len = _dist(brow_l_out, brow_l_in)
    brow_r_len = _dist(brow_r_out, brow_r_in)
    features.append(brow_l_len / ipd)               # 左眉長
    features.append(brow_r_len / ipd)               # 右眉長
    features.append(_dist(brow_l_in, l_eye_top) / ipd)  # 左眉-目 距離
    features.append(_dist(brow_r_in, r_eye_top) / ipd)  # 右眉-目 距離

    # === 追加: 左右対称性 (4次元) ===
    face_cx = (cheek_l[0] + cheek_r[0]) / 2
    sym_nose = abs(nose_tip[0] - face_cx) / (face_w + 1e-9)
    sym_mouth = abs(mouth_center[0] - face_cx) / (face_w + 1e-9)
    sym_eye_h = abs(l_eye_h - r_eye_h) / (ipd + 1e-9)
    sym_brow = abs(brow_l_len - brow_r_len) / (ipd + 1e-9)
    features.append(sym_nose)
    features.append(sym_mouth)
    features.append(sym_eye_h)
    features.append(sym_brow)

    # === 追加: 顎・輪郭 (4次元) ===
    features.append(_angle_deg(jaw_l, chin, jaw_r))       # 顎角度
    features.append(_dist(jaw_l, jaw_r) / (face_w + 1e-9))  # 顎幅比
    features.append(_dist(chin, mouth_center) / (face_h + 1e-9))  # 顎-口距離比
    features.append(_dist(forehead, eye_center) / (face_h + 1e-9))  # 額-目距離比

    # === 追加: パーツ間角度 (4次元) ===
    features.append(_angle_deg(l_eye, nose_root, r_eye))
    features.append(_angle_deg(mouth_l, chin, mouth_r))
    features.append(_angle_deg(brow_l_out, forehead, brow_r_out))
    features.append(_angle_deg(l_eye, mouth_center, r_eye))

    return np.array(features, dtype=np.float32)


class ExtendedEmbedder(FaceEmbedder):
    name = "extended"

    def embed(self, image_path: str) -> np.ndarray | None:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        result = get_detector().detect(image_bytes)
        return extract_extended_features(result)
