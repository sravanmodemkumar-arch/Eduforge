import logging
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


class EmailProvider:
    """Send emails via SendGrid v3 API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME

    async def send(
        self,
        recipient_id: str,
        body: str,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Send an email via SendGrid.

        Args:
            recipient_id: The recipient's email address.
            body: The email body (HTML supported).
            variables: Optional dict; may contain ``subject`` key.

        Returns:
            The SendGrid ``X-Message-Id`` header value.

        Raises:
            ProviderError: If the API call fails.
        """
        variables = variables or {}
        subject = variables.get("subject", "Notification from EduForge")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "personalizations": [
                {
                    "to": [{"email": recipient_id}],
                    "subject": subject,
                }
            ],
            "from": {"email": self.from_email, "name": self.from_name},
            "content": [
                {"type": "text/html", "value": body},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    SENDGRID_API_URL, json=payload, headers=headers
                )
                response.raise_for_status()
                message_id: str = response.headers.get(
                    "X-Message-Id", "unknown"
                )
                logger.info(
                    "Email sent via SendGrid: %s to %s",
                    message_id,
                    recipient_id,
                )
                return message_id
        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            logger.error(
                "SendGrid API error: %s – %s",
                exc.response.status_code,
                error_body,
            )
            raise ProviderError(
                f"SendGrid API returned {exc.response.status_code}: {error_body}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("SendGrid request failed: %s", exc)
            raise ProviderError(f"SendGrid request failed: {exc}") from exc
