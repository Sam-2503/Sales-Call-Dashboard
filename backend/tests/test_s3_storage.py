from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from analyser_api.storage.s3 import S3Storage


@pytest.mark.asyncio
async def test_s3_storage_round_trip_ranges_and_prefix_delete(tmp_path: Path) -> None:
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        storage = S3Storage("test-bucket", region_name="us-east-1")
        source = tmp_path / "source.bin"
        source.write_bytes(b"0123456789")
        await storage.put("workspace/call/original.wav", source)
        assert await storage.size("workspace/call/original.wav") == 10
        assert await storage.open_range("workspace/call/original.wav", 2, 5) == b"2345"
        await storage.healthcheck()
        await storage.delete_prefix("workspace/call")
        with pytest.raises(ClientError):
            await storage.size("workspace/call/original.wav")
