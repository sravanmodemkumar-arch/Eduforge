import logging
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


class SMSProvider:
    """Send SMS messages via MSG91."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_url = settings.MSG91_API_URL
        self.auth_key = settings.MSG91_AUTH_KEY
        self.sender_id = settings.MSG91_SENDER_ID
        self.dle_te_id = settings.MSG91_DLT_TE_ID

    async def send(
        self,
        recipient_id: str,
        body: str,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Send an SMS via MSG91.

        Args:
            recipient_id: Mobile number with country code (e.g. "919876543210").
            body: The SMS body text.
            variables: Optional template variables for MSG91 flow-based sending.

        Returns:
            The MSG91 request ID.

        Raises:
            ProviderError: If the API call fails.
        """
        url = f"{self.api_url}/flow/"
        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "sender": self.sender_id,
            "otp": False,
            "recipients": [
                {
                    "mobiles": recipient_id,
                    "body": body,
                    **(variables or {}),
                }
            ],
        }

        if self.dle_te_id:
            payload["DLT_TE_ID"] = self.dle_te_id

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                request_id: str = data.get("request_id", data.get("message", "unknown"))
                logger.info("SMS sent via MSG91: %s to %s", request_id, recipient_id)
                return request_id
        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            logger.error("MSG91 API error: %s – %s", exc.response.status_code, error_body)
            raise ProviderError(
                f"MSG91 API returned {exc.response.status_code}: {error_body}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("MSG91 request failed: %s", exc)
            raise ProviderError(f"MSG91 request failed: {exc}") from exc
