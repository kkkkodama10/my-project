"""Phase 3: 画像アップロードサービス（S3 / ローカル対応）。

環境変数 S3_BUCKET_NAME が設定されている場合は S3 にアップロード、
未設定の場合はローカルの uploads/ ディレクトリに保存します。
"""

import os
from pathlib import Path
from uuid import uuid4

from app.config import CLOUDFRONT_DOMAIN, S3_BUCKET_NAME, UPLOADS_DIR


def _get_file_extension(filename: str) -> str:
    """ファイル拡張子を取得。"""
    return Path(filename).suffix.lower()


async def upload_image(file_data: bytes, filename: str, content_type: str) -> str:
    """画像をアップロードしてURLを返す。

    Args:
        file_data: ファイルのバイナリデータ
        filename: 元のファイル名
        content_type: コンテンツタイプ (例: "image/jpeg")

    Returns:
        str: 画像のURL
    """
    ext = _get_file_extension(filename)
    unique_filename = f"{uuid4()}{ext}"

    # S3 が設定されている場合は S3 にアップロード
    if S3_BUCKET_NAME:
        return await _upload_to_s3(file_data, unique_filename, content_type)

    # ローカルに保存
    return await _upload_to_local(file_data, unique_filename)


async def _upload_to_s3(
    file_data: bytes,
    filename: str,
    content_type: str,
) -> str:
    """S3に画像をアップロード。

    Args:
        file_data: ファイルのバイナリデータ
        filename: S3に保存するファイル名
        content_type: コンテンツタイプ

    Returns:
        str: CloudFront または S3 の URL
    """
    import boto3

    s3_client = boto3.client("s3")
    key = f"images/{filename}"

    # S3にアップロード
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=file_data,
        ContentType=content_type,
    )

    # CloudFrontドメインが設定されていればCloudFront URL、なければS3 URL
    if CLOUDFRONT_DOMAIN:
        return f"https://{CLOUDFRONT_DOMAIN}/{key}"
    else:
        region = os.getenv("AWS_REGION", "ap-northeast-1")
        return f"https://{S3_BUCKET_NAME}.s3.{region}.amazonaws.com/{key}"


async def _upload_to_local(file_data: bytes, filename: str) -> str:
    """ローカルディレクトリに画像を保存。

    Args:
        file_data: ファイルのバイナリデータ
        filename: 保存するファイル名

    Returns:
        str: ローカルのURL（/uploads/...）
    """
    file_path = UPLOADS_DIR / filename

    # ファイルを保存
    with open(file_path, "wb") as f:
        f.write(file_data)

    # ローカルURLを返す
    return f"/uploads/{filename}"


async def delete_image(image_url: str) -> None:
    """画像を削除。

    Args:
        image_url: 削除する画像のURL
    """
    # S3の画像の場合
    if S3_BUCKET_NAME and (
        CLOUDFRONT_DOMAIN in image_url
        or S3_BUCKET_NAME in image_url
    ):
        await _delete_from_s3(image_url)
    # ローカルの画像の場合
    elif image_url.startswith("/uploads/"):
        await _delete_from_local(image_url)


async def _delete_from_s3(image_url: str) -> None:
    """S3から画像を削除。

    Args:
        image_url: S3またはCloudFrontのURL
    """
    import boto3

    # URLからキーを抽出
    # 例: https://dxxxx.cloudfront.net/images/abc.jpg -> images/abc.jpg
    if "/images/" in image_url:
        key = "images/" + image_url.split("/images/")[-1]
    else:
        return  # キーが不明な場合はスキップ

    s3_client = boto3.client("s3")
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
    except Exception as e:
        print(f"[ImageService] Failed to delete from S3: {e}")


async def _delete_from_local(image_url: str) -> None:
    """ローカルから画像を削除。

    Args:
        image_url: ローカルURL（/uploads/...）
    """
    filename = image_url.replace("/uploads/", "")
    file_path = UPLOADS_DIR / filename

    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"[ImageService] Failed to delete from local: {e}")
