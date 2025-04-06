import os
import tempfile
from PIL import Image
from memory_profiler import profile

# 画像のモックデータを作成する関数
def create_mock_images(num_images, image_size=(100, 100), directory=None):
    if directory is None:
        directory = tempfile.mkdtemp()
    image_paths = []
    for i in range(num_images):
        # 単色の画像を生成
        img = Image.new("RGB", image_size, color=(i % 256, (i * 2) % 256, (i * 3) % 256))
        path = os.path.join(directory, f"mock_{i}.jpg")
        img.save(path, "JPEG")
        image_paths.append(path)
    return image_paths

# lazy loading: 画像パスから必要なときに画像を読み込むジェネレータ
def load_images_lazy(image_paths):
    for path in image_paths:
        with Image.open(path) as img:
            # 必要なら画像処理（ここでは load() で読み込みを強制）
            img.load()
            yield img.copy()  # with ブロック終了後にアクセスできるよう copy() を返す

# 一括読み込み: 全画像を一度にメモリに展開する
def load_images_all(image_paths):
    images = []
    for path in image_paths:
        with Image.open(path) as img:
            img.load()
            images.append(img.copy())
    return images

@profile
def process_images_lazy(image_paths):
    # lazy loadingで画像を順次読み込み処理を実施
    for img in load_images_lazy(image_paths):
        # ここで何らかの画像処理を実施（例として画像サイズを取得）
        _ = img.size

@profile
def process_images_all(image_paths):
    # 一括読み込みで全画像を読み込む
    images = load_images_all(image_paths)
    for img in images:
        _ = img.size

if __name__ == "__main__":
    # モック画像データの作成（例として100枚）
    num_images = 100000
    image_paths = create_mock_images(num_images)
    print(f"Mock images created in directory: {os.path.dirname(image_paths[0])}")

    print("Processing images with lazy loading:")
    process_images_lazy(image_paths)

    print("Processing images with all-at-once loading:")
    process_images_all(image_paths)