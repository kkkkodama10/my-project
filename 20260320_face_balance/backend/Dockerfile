FROM python:3.11-slim

WORKDIR /app

# OpenCV / MediaPipe / dlib が必要とするシステムライブラリとビルドツール
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    cmake \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 依存関係を先にコピーしてキャッシュを最適化
COPY requirements.txt .

# dlib のビルドはメモリ消費が大きいため:
# 1. 並列度を1に制限
# 2. GUI サポートを無効化
# 3. 最適化を無効化してメモリ消費を抑制
# ※ Docker Desktop のメモリ割り当てを 6GB 以上にしてください
RUN MAKEFLAGS="-j1" CMAKE_BUILD_PARALLEL_LEVEL=1 \
    DLIB_NO_GUI_SUPPORT=1 \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
