"""S3-compatible audio storage using boto3 off the event loop."""

from __future__ import annotations

import asyncio
from pathlib import Path

import boto3
from botocore.config import Config


class S3Storage:
    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        region_name: str = "auto",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    async def put(self, key: str, path: Path) -> None:
        await asyncio.to_thread(self.client.upload_file, str(path), self.bucket, key)

    async def open_range(self, key: str, start: int, end: int) -> bytes:
        response = await asyncio.to_thread(
            self.client.get_object,
            Bucket=self.bucket,
            Key=key,
            Range=f"bytes={start}-{end}",
        )
        return await asyncio.to_thread(response["Body"].read)

    async def size(self, key: str) -> int:
        response = await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=key)
        return int(response["ContentLength"])

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)

    async def delete_prefix(self, prefix: str) -> None:
        response = await asyncio.to_thread(
            self.client.list_objects_v2, Bucket=self.bucket, Prefix=prefix
        )
        objects = [{"Key": item["Key"]} for item in response.get("Contents", [])]
        if objects:
            await asyncio.to_thread(
                self.client.delete_objects,
                Bucket=self.bucket,
                Delete={"Objects": objects},
            )

    async def healthcheck(self) -> None:
        await asyncio.to_thread(self.client.head_bucket, Bucket=self.bucket)
