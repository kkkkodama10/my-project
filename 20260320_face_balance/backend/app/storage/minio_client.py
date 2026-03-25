import io
import threading

import boto3
from botocore.exceptions import ClientError

from app.config import settings

_client = None
_lock = threading.Lock()


def get_storage_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:  # double-checked locking
                _client = _StorageClient()
    return _client


class _StorageClient:
    def __init__(self) -> None:
        self._s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
        )
        self._bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("404", "NoSuchBucket"):
                self._s3.create_bucket(Bucket=self._bucket)
            else:
                # 認証エラー・接続エラーなどは上位に伝播させる
                raise

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        self._s3.upload_fileobj(
            io.BytesIO(data),
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    def download(self, key: str) -> bytes:
        buf = io.BytesIO()
        self._s3.download_fileobj(self._bucket, key, buf)
        return buf.getvalue()

    def delete(self, key: str) -> None:
        # S3/MinIO の delete_object は存在しないキーでも 204 を返すためエラーにならない
        self._s3.delete_object(Bucket=self._bucket, Key=key)
