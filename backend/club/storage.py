"""Private storage adapter. URLs are never inferred from database keys."""

from pathlib import Path
import io
import boto3
from django.conf import settings


def client():
    return boto3.client(
        's3', endpoint_url=settings.S3_ENDPOINT_URL, region_name=settings.AWS_DEFAULT_REGION
    )


def local_path(key):
    root = settings.STORAGE_ROOT.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Invalid storage key')
    return path


def put(key, data, content_type):
    if settings.S3_BUCKET:
        client().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    else:
        path = local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def get(key):
    if settings.S3_BUCKET:
        return client().get_object(Bucket=settings.S3_BUCKET, Key=key)['Body'].read()
    return local_path(key).read_bytes()


def stream(key):
    if settings.S3_BUCKET:
        return io.BytesIO(get(key))
    return local_path(key).open('rb')
