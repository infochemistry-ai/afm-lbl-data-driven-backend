import io
from typing import BinaryIO

import boto3


class S3Storage:
    backend_name = "s3"

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        presign_expires_sec: int = 3600,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.lstrip("/")
        self.presign_expires_sec = presign_expires_sec
        kwargs = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if access_key_id and secret_access_key:
            kwargs["aws_access_key_id"] = access_key_id
            kwargs["aws_secret_access_key"] = secret_access_key
        self.client = boto3.client("s3", **kwargs)

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}" if self.prefix else key

    def put(self, key: str, data: BinaryIO) -> None:
        self.client.upload_fileobj(data, self.bucket, self._full_key(key))

    def open(self, key: str) -> BinaryIO:
        obj = self.client.get_object(Bucket=self.bucket, Key=self._full_key(key))
        return io.BytesIO(obj["Body"].read())

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._full_key(key))
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._full_key(key))

    def url(self, key: str, expires_sec: int | None = None) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": self._full_key(key)},
            ExpiresIn=expires_sec or self.presign_expires_sec,
        )
