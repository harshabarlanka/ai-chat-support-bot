import boto3

from app.config import settings

s3_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)


def upload_file_to_s3(file_bytes: bytes, key: str, content_type: str) -> None:
    s3_client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )


def download_file_from_s3(key: str) -> bytes:
    response = s3_client.get_object(Bucket=settings.s3_bucket_name, Key=key)
    return response["Body"].read()


def delete_file_from_s3(key: str) -> None:
    s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=key)