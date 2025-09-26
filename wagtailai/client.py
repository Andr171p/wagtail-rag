from typing import Any

import logging

import requests

from .utils import get_rag_settings

logger = logging.getLogger(__name__)


class RAGClient:
    def __init__(self) -> None:
        self.settings = get_rag_settings()

    def index_page(self, page_json: dict[str, Any]) -> None:
        try:
            with requests.Session() as session:
                response = session.post(
                    url=f"{self.settings.base_url}/api/v1/pages",
                    headers={"Content-Type": "application/json"},
                    json=page_json,
                    timeout=self.settings.timeout,
                )
                response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.exception("Failed to index page, error: {e}")

    def ask_ai(self, session_id: str, text: str) -> str | None:
        try:
            with requests.Session() as session:
                response = session.post(
                    url=f"{self.settings.base_url}/api/v1/rag",
                    headers={"Content-Type": "application/json"},
                    json={"role": "user", "session_id": session_id, "text": text},
                )
                response.raise_for_status()
            return response.json().get("text")
        except requests.exceptions.RequestException:
            logger.exception("Failed to ask rag, error: {e}")
