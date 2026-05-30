import io

import boto3
import pytest
from moto import mock_aws

from app.storage.s3 import S3Storage


@pytest.fixture
def s3_bucket():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        yield client


def test_s3_put_get_delete(s3_bucket):
    s = S3Storage(bucket="test-bucket", prefix="", region="us-east-1")
    s.put("scans/abc.txt", io.BytesIO(b"hello"))
    assert s.exists("scans/abc.txt")
    with s.open("scans/abc.txt") as f:
        assert f.read() == b"hello"
    s.delete("scans/abc.txt")
    assert not s.exists("scans/abc.txt")


def test_s3_url_is_presigned(s3_bucket):
    s = S3Storage(bucket="test-bucket", prefix="", region="us-east-1")
    s.put("scans/abc.txt", io.BytesIO(b"hi"))
    url = s.url("scans/abc.txt", expires_sec=60)
    assert "X-Amz-Signature" in url or "Signature" in url


def test_s3_applies_prefix(s3_bucket):
    s = S3Storage(bucket="test-bucket", prefix="afm-prod/", region="us-east-1")
    s.put("scans/abc.txt", io.BytesIO(b"x"))
    obj = boto3.client("s3", region_name="us-east-1").get_object(
        Bucket="test-bucket", Key="afm-prod/scans/abc.txt"
    )
    assert obj["Body"].read() == b"x"
