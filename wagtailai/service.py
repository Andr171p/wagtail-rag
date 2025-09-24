from typing import Any

import logging

import requests

logger = logging.getLogger(__name__)


def store_published_page(ai_page_json: dict[str, Any]) -> None:
    try:
        with requests.Session() as session:
            response = session.post(
                url="http://localhost:8000/api/v1/pages",
                headers={"Content-Type": "application/json"},
                json=ai_page_json,
                timeout=30,
            )
            response.raise_for_status()
    except requests.exceptions.RequestException:
        logger.exception("Failed to store page, error: {e}")
