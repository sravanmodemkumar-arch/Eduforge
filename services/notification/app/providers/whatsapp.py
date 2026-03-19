import logging
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


class WhatsAppProvider:
    """Send messages via Meta WhatsApp Business API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN

    async def send(
        self,
        recipient_id: str,
        body: str,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Send a WhatsApp text message.

        Args:
            recipient_id: The recipient's phone number in international format.
            body: The message body text.
            variables: Optional variables (unused for direct text, reserved for
                       template messages).

        Returns:
            The WhatsApp message ID from Meta's API.

        Raises:
            ProviderError: If the API call fails.
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                message_id: str = data["messages"][0]["id"]
                logger.info(
                    "WhatsApp message sent: %s to %s",
                    message_id,
                    recipient_id,
                )
                return message_id
        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            logger.error("WhatsApp API error: %s – %s", exc.response.status_code, error_body)
            raise ProviderError(
                f"WhatsApp API returned {exc.response.status_code}: {error_body}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("WhatsApp request failed: %s", exc)
            raise ProviderError(f"WhatsApp request failed: {exc}") from exc
