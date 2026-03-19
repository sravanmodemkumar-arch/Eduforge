"""Cloudflare R2 storage client built on boto3."""

from __future__ import annotations

import os
from typing import Any

import boto3
from botocore.config import Config


class R2Client:
    """Thin wrapper around an S3-compatible client pointed at Cloudflare R2.

    Required environment variables::

        CLOUDFLARE_R2_ACCOUNT_ID
        CLOUDFLARE_R2_ACCESS_KEY
        CLOUDFLARE_R2_SECRET_KEY
    """

    def __init__(self) -> None:
        account_id = os.environ["CLOUDFLARE_R2_ACCOUNT_ID"]
        self._endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self._client = boto3.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=os.environ["CLOUDFLARE_R2_ACCESS_KEY"],
            aws_secret_access_key=os.environ["CLOUDFLARE_R2_SECRET_KEY"],
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def upload_file(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Upload *body* bytes to *bucket*/*key* and return the S3 response."""
        extra: dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra["Metadata"] = metadata
        return self._client.put_object(Bucket=bucket, Key=key, Body=body, **extra)

    def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned GET URL valid for *expires_in* seconds (default 1 h)."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_file(self, bucket: str, key: str) -> dict[str, Any]:
        """Delete the object at *bucket*/*key*."""
        return self._client.delete_object(Bucket=bucket, Key=key)
