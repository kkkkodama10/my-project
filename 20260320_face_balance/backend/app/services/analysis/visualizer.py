import io

import cv2
import numpy as np
from PIL import Image as PILImage

from app.services.analysis.detectors.base import LandmarkResult


def draw_landmarks(image_bytes: bytes, landmark_result: LandmarkResult) -> bytes:
    """元画像に MediaPipe ランドマーク点と顔BBoxを重ねた JPEG を返す。

    - 顔1件検出: 468点の緑ドット + 赤いBBox矩形
    - 顔未検出 / 複数顔: テキストオーバーレイのみ
    """
    pil = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    img = cv2.cvtColor(np.array(pil, dtype=np.uint8), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]

    if landmark_result.face_count == 1:
        lm = landmark_result.landmarks  # shape: (468, 3), 値は 0.0～1.0 の正規化座標
        xs = (lm[:, 0] * w).astype(int)
        ys = (lm[:, 1] * h).astype(int)

        # 顔BBox（赤）
        x1, y1, x2, y2 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # ランドマーク点（緑）
        for x, y in zip(xs.tolist(), ys.tolist()):
            cv2.circle(img, (x, y), 2, (0, 255, 0), -1)

    elif landmark_result.face_count == 0:
        _put_overlay_text(img, "No face detected")
    else:
        _put_overlay_text(img, f"Multiple faces ({landmark_result.face_count})")

    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return bytes(buf)


def _put_overlay_text(img: np.ndarray, text: str) -> None:
    """半透明な背景付きテキストを画像左上に描画する。"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.8, img.shape[1] / 800)
    thickness = 2
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)

    # 半透明背景
    overlay = img.copy()
    cv2.rectangle(overlay, (10, 10), (tw + 20, th + baseline + 20), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

    # テキスト（オレンジ）
    cv2.putText(img, text, (15, th + 15), font, scale, (0, 140, 255), thickness)
