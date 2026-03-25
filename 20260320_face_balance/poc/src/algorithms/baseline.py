"""Baseline: MediaPipe Tasks API + 15次元手設計特徴量 + コサイン類似度"""
import io
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from detector import get_detector, LandmarkResult
from .base import FaceEmbedder

# ランドマークインデックス（backend と同一）
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


def extract_features(result: LandmarkResult) -> np.ndarray | None:
    """LandmarkResult から 15次元特徴量ベクトルを返す。顔未検出は None。"""
    if result.face_count != 1:
        return None
    lm = result.landmarks

    l_eye = _pt(lm, _L_EYE_OUTER)
    r_eye = _pt(lm, _R_EYE_OUTER)
    ipd = _dist(l_eye, r_eye)
    if ipd < 1e-9:
        return None

    nose_tip    = _pt(lm, _NOSE_TIP)
    nose_root   = _pt(lm, _NOSE_ROOT)
    nose_base   = _pt(lm, _NOSE_BASE)
    mouth_l     = _pt(lm, _MOUTH_L)
    mouth_r     = _pt(lm, _MOUTH_R)
    cheek_l     = _pt(lm, _CHEEK_L)
    cheek_r     = _pt(lm, _CHEEK_R)
    forehead    = _pt(lm, _FOREHEAD)
    chin        = _pt(lm, _CHIN)
    brow_l_in   = _pt(lm, _BROW_L_INNER)
    brow_r_in   = _pt(lm, _BROW_R_INNER)
    brow_l_out  = _pt(lm, _BROW_L_OUTER)

    # 距離 5次元
    nose_length = _dist(nose_root, nose_tip) / ipd
    mouth_width = _dist(mouth_l, mouth_r) / ipd
    face_width  = _dist(cheek_l, cheek_r) / ipd
    brow_gap    = _dist(brow_l_in, brow_r_in) / ipd
    eye_mouth_v = _dist((l_eye + r_eye) / 2, (mouth_l + mouth_r) / 2) / ipd

    # 角度 3次元
    ang_eye_nose_eye     = _angle_deg(l_eye, nose_tip, r_eye)
    ang_mouth_nose_mouth = _angle_deg(mouth_l, nose_tip, mouth_r)
    ang_brow_eye_nose    = _angle_deg(brow_l_out, l_eye, nose_root)

    # 比率 7次元
    face_h   = _dist(forehead, chin)
    face_w   = _dist(cheek_l, cheek_r)
    nose_len = _dist(nose_root, nose_tip)
    mouth_w  = _dist(mouth_l, mouth_r)

    face_aspect   = face_h / (face_w + 1e-9)
    eye_face      = ipd / (face_w + 1e-9)
    nose_face     = nose_len / (face_h + 1e-9)
    mouth_ipd     = mouth_w / (ipd + 1e-9)

    upper  = _dist(forehead, nose_root)
    middle = _dist(nose_root, nose_base)
    lower  = _dist(nose_base, chin)
    total  = upper + middle + lower + 1e-9

    return np.array([
        nose_length, mouth_width, face_width, brow_gap, eye_mouth_v,
        ang_eye_nose_eye, ang_mouth_nose_mouth, ang_brow_eye_nose,
        face_aspect, eye_face, nose_face, mouth_ipd,
        upper / total, middle / total, lower / total,
    ], dtype=np.float32)


class BaselineEmbedder(FaceEmbedder):
    name = "baseline"

    def embed(self, image_path: str) -> np.ndarray | None:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        result = get_detector().detect(image_bytes)
        return extract_features(result)
