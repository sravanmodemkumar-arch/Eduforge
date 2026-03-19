"""AWS SQS helper client."""

from __future__ import annotations

import json
import os
from typing import Any

import boto3


class SQSClient:
    """Convenience wrapper around the boto3 SQS client.

    Uses the standard ``AWS_REGION`` (default ``us-east-1``),
    ``AWS_ACCESS_KEY_ID``, and ``AWS_SECRET_ACCESS_KEY`` environment variables.
    """

    def __init__(self) -> None:
        self._client = boto3.client(
            "sqs",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
        self._queue_url_cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_queue_url(self, queue_name: str) -> str:
        if queue_name not in self._queue_url_cache:
            resp = self._client.get_queue_url(QueueName=queue_name)
            self._queue_url_cache[queue_name] = resp["QueueUrl"]
        return self._queue_url_cache[queue_name]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_message(self, queue_name: str, body: dict) -> dict[str, Any]:
        """Serialize *body* as JSON and send it to *queue_name*."""
        return self._client.send_message(
            QueueUrl=self._get_queue_url(queue_name),
            MessageBody=json.dumps(body),
        )

    def receive_messages(
        self,
        queue_name: str,
        max: int = 10,
        wait_time: int = 5,
    ) -> list[dict[str, Any]]:
        """Receive up to *max* messages from *queue_name*.

        Each returned dict contains ``MessageId``, ``Body`` (parsed from JSON),
        and ``ReceiptHandle``.
        """
        resp = self._client.receive_message(
            QueueUrl=self._get_queue_url(queue_name),
            MaxNumberOfMessages=min(max, 10),
            WaitTimeSeconds=wait_time,
        )
        messages = resp.get("Messages", [])
        for msg in messages:
            try:
                msg["Body"] = json.loads(msg["Body"])
            except (json.JSONDecodeError, TypeError):
                pass  # leave Body as-is if it is not valid JSON
        return messages

    def delete_message(self, queue_name: str, receipt_handle: str) -> dict[str, Any]:
        """Delete a message identified by *receipt_handle* from *queue_name*."""
        return self._client.delete_message(
            QueueUrl=self._get_queue_url(queue_name),
            ReceiptHandle=receipt_handle,
        )
