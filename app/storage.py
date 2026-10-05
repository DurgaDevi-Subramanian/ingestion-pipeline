import hashlib
import mimetypes
import os
from urllib.parse import quote

import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.environ["S3_BUCKET"]
s3 = boto3.client("s3")


def make_doc_id(file_path: str) -> str:
    """Short fingerprint of the file's contents."""
    return hashlib.sha256(open(file_path, "rb").read()).hexdigest()[:10]


def upload_file(local_path: str, key: str, metadata: dict | None = None,
                tags: dict | None = None) -> str:
    """Upload one file, encrypted, with metadata and tags. Returns its s3:// link."""
    extra = {"ServerSideEncryption": "AES256"}

    if local_path.endswith(".md"):
        extra["ContentType"] = "text/markdown; charset=utf-8"
    else:
        guessed = mimetypes.guess_type(local_path)[0]
        if guessed:
            extra["ContentType"] = guessed

    if metadata:
        extra["Metadata"] = {k: str(v) for k, v in metadata.items()}
    if tags:
        extra["Tagging"] = "&".join(f"{quote(k)}={quote(str(v))}" for k, v in tags.items())

    s3.upload_file(local_path, BUCKET, key, ExtraArgs=extra)
    return f"s3://{BUCKET}/{key}"


def presigned_url(key: str, seconds: int = 3600) -> str:
    """Temporary link to a private object (we'll use this in the API)."""
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=seconds
    )