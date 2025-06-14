import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ------------- 基本設定 --------------------------------------------------------
FPS, DURATION_SEC = 10, 10
N_FRAMES = FPS * DURATION_SEC

# Ground Truth (ここで y も動かす) --------------------------------------------
x_true = np.linspace(0, 10, N_FRAMES)
y_true = np.linspace(0,  5, N_FRAMES)      # 例：斜めに上昇

# 観測（ノイズ付き） -----------------------------------------------------------
np.random.seed(0)
noise_std = 0.3
x_meas = x_true + np.random.normal(0, noise_std, N_FRAMES)
y_meas = y_true + np.random.normal(0, noise_std, N_FRAMES)

# ---------- 1D カルマンフィルタを x・y で2本走らせる --------------------------
def kalman_1d(zs, motion, motion_var, meas_var, mu0=0.0, sig0=1.0):
    mu, sig = mu0, sig0
    mu_hist = []
    for z in zs:
        # update
        mu = (sig * z + meas_var * mu) / (sig + meas_var)
        sig = 1 / (1 / sig + 1 / meas_var)
        mu_hist.append(mu)
        # predict
        mu += motion
        sig += motion_var
    return np.array(mu_hist)

# モデルパラメータ
vx = (x_true[1] - x_true[0])          # x方向速度
vy = (y_true[1] - y_true[0])          # y方向速度
motion_var = 100
meas_var   = noise_std**2

x_pred = kalman_1d(x_meas, vx, motion_var, meas_var)
y_pred = kalman_1d(y_meas, vy, motion_var, meas_var)

# ------------ 可視化（真値・測定・予測を重ねる） ------------------------------
fig, ax = plt.subplots(figsize=(5, 5))
ax.set_xlim(-1, 11)
ax.set_ylim(-1, 6)
ax.set_aspect('equal'); ax.grid(True)
ax.set_title("2-D Kalman Filter : Ground Truth vs Prediction")

true_dot, = ax.plot([], [], 'o', label="Truth")
meas_dot, = ax.plot([], [], 'x', label="Measured")
pred_dot, = ax.plot([], [], 'o', color='red', alpha=.6, label="Kalman")
ax.legend(loc="upper left")

def init():
    true_dot.set_data([], [])
    meas_dot.set_data([], [])
    pred_dot.set_data([], [])
    return true_dot, meas_dot, pred_dot

def update(f):
    true_dot.set_data([x_true[f]], [y_true[f]])
    meas_dot.set_data([x_meas[f]], [y_meas[f]])
    pred_dot.set_data([x_pred[f]], [y_pred[f]])
    return true_dot, meas_dot, pred_dot

ani = animation.FuncAnimation(
    fig, update, frames=N_FRAMES,
    init_func=init, blit=True, interval=1000/FPS
)

ani.save(
    "kalman_2d_overlay_2.mp4",
    writer=animation.FFMpegWriter(fps=FPS)
)
print("✅ kalman_2d_overlay.mp4 を保存しました")
