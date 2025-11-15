from typing import Any, Dict, List
import logging

import httpx


logger = logging.getLogger("aurora_app")


class AuroraMessagesClient:
    """
    Client for the public Aurora messages API.

    It is resilient to API failures:
    - On network / HTTP errors, it logs the issue and returns an empty list
      instead of crashing the whole application.
    """

    def __init__(
        self,
        base_url: str = "http://november7-730026606190.europe-west1.run.app",
        timeout: float = 20.0,
    ) -> None:
        # Normalise base URL
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_messages(self) -> List[Dict[str, Any]]:
        """
        Fetch all messages from the Aurora public API.

        Handles:
        - redirects (302 / 307, etc.)
        - payloads shaped like:
            * {"messages": [ ... ]}
            * {"data": [ ... ]}
            * a plain list [ ... ]
            * a single dict { ... }  (wrapped into a list)
        - HTTP errors by returning [] and logging.
        """
        url = f"{self.base_url}/messages/"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)
        except httpx.HTTPError as exc:
            logger.error("HTTP error when calling Aurora messages API: %s", exc)
            return []

        if not (200 <= resp.status_code < 300):
            logger.error(
                "Aurora messages API returned %s for %s. Body: %r",
                resp.status_code,
                resp.url,
                resp.text,
            )
            # Return empty list so the app can still run
            return []

        # Try to parse JSON
        try:
            payload = resp.json()
        except ValueError as exc:
            logger.error("Failed to parse JSON from Aurora messages API: %s", exc)
            return []

        items: List[Any] = []

        # 1) If it's already a list, use it directly
        if isinstance(payload, list):
            items = payload

        # 2) If it's a dict, try to find any list inside (messages, data, etc.)
        elif isinstance(payload, dict):
            list_found = False
            for value in payload.values():
                if isinstance(value, list):
                    items = value
                    list_found = True
                    break

            # If no list is found, treat the whole dict as a single message
            if not list_found:
                items = [payload]

        # 3) Any other type: wrap as a single item
        else:
            items = [payload]

        # Normalise so every item is a dict
        normalized: List[Dict[str, Any]] = []
        for item in items:
            if isinstance(item, dict):
                normalized.append(item)
            else:
                normalized.append({"_value": item})

        return normalized
