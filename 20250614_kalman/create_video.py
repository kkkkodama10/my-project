"""
10 秒（100 フレーム）でボールが x=0→10 を直線移動する動画を作成し、
MP4 形式で保存するサンプルスクリプト。
※ FFmpeg がインストールされている環境ならそのまま動きます。
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- パラメータ設定 -----------------------------------------------------------
FPS          = 10           # フレームレート
DURATION_SEC = 10           # 動画の長さ [秒]
N_FRAMES     = FPS * DURATION_SEC

# ボールの軌道（今回は単純な直線）---------------------------------------------
x_path = np.linspace(0, 10, N_FRAMES)    # x は 0→10 へ等速
y_path = np.zeros_like(x_path)           # y = 0 （水平線上）

# --- 描画準備 -----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5, 5))
ax.set_xlim(-1, 11)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")
ax.grid(True)

# ボールを表す散布図（初期位置を設定）
ball, = ax.plot([], [], "o", markersize=12, lw=0, label="ball")

def init():
    """FuncAnimation 用の初期化関数"""
    ball.set_data([], [])
    return (ball,)

def update(frame):
    ball.set_data([x_path[frame]], [y_path[frame]])
    return (ball,)

# --- アニメーション生成 & 保存 -----------------------------------------------
ani = animation.FuncAnimation(
    fig,
    update,
    frames=N_FRAMES,
    init_func=init,
    blit=True,
    interval=1000 / FPS,  # ミリ秒
)

# FFmpeg を使って MP4 保存
# もし PillowWriter で GIF を作りたい場合はコメントアウトして下を使う
ani.save(
    "ball_motion.mp4",
    writer=animation.FFMpegWriter(fps=FPS, bitrate=1800),
)

# --- GIF 保存例 ---------------------------------------------------------------
# ani.save(
#     "ball_motion.gif",
#     writer=animation.PillowWriter(fps=FPS),
# )

print("📽️  保存完了: ball_motion.mp4")
