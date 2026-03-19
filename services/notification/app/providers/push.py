import json
import logging
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


class PushProvider:
    """Send push notifications via Firebase Cloud Messaging (HTTP v1 API)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.project_id = settings.FIREBASE_PROJECT_ID
        self.credentials_path = settings.FIREBASE_CREDENTIALS_PATH
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """
        Obtain an OAuth2 access token from the Firebase service account
        credentials using the google-auth library.
        """
        if self._access_token:
            return self._access_token

        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            credentials.refresh(Request())
            self._access_token = credentials.token
            return self._access_token  # type: ignore[return-value]
        except Exception as exc:
            logger.error("Failed to obtain Firebase access token: %s", exc)
            raise ProviderError(
                f"Firebase auth failed: {exc}"
            ) from exc

    async def send(
        self,
        recipient_id: str,
        body: str,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Send a push notification via FCM HTTP v1 API.

        Args:
            recipient_id: The FCM device registration token.
            body: Notification body text.
            variables: Optional dict; may contain ``title`` and ``data`` keys.

        Returns:
            The FCM message name (projects/{id}/messages/{id}).

        Raises:
            ProviderError: If the API call fails.
        """
        variables = variables or {}
        title = variables.get("title", "EduForge")
        data = variables.get("data", {})

        access_token = await self._get_access_token()
        url = (
            f"https://fcm.googleapis.com/v1/projects/{self.project_id}"
            f"/messages:send"
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "message": {
                "token": recipient_id,
                "notification": {
                    "title": title,
                    "body": body,
                },
                "data": {k: str(v) for k, v in data.items()} if data else {},
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                message_name: str = result.get("name", "unknown")
                logger.info(
                    "Push notification sent via FCM: %s to token %s…",
                    message_name,
                    recipient_id[:20],
                )
                return message_name
        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            logger.error(
                "FCM API error: %s – %s",
                exc.response.status_code,
                error_body,
            )
            # Invalidate token on auth errors so it is refreshed next time
            if exc.response.status_code == 401:
                self._access_token = None
            raise ProviderError(
                f"FCM API returned {exc.response.status_code}: {error_body}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("FCM request failed: %s", exc)
            raise ProviderError(f"FCM request failed: {exc}") from exc
