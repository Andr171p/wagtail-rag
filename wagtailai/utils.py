import hashlib
import json

from wagtail.models import Page


def get_page_hash(page: Page) -> str:
    """Генерирует хэш контента страницы для отслеживания изменений"""
    content: dict[str, str] = {
        "id": page.id,
        "title": page.title,
        "url": page.full_url,
        "content": "",
        "type": "page",
        "last_updated": page.last_published_at.isoformat() if page.last_published_at else None,
        "language": getattr(page, "locale", "en"),
    }
    if hasattr(page, "get_searchable_content"):
        search_content = page.get_searchable_content()
        content["content"] = " ".join(search_content)
    content_string = json.dumps(content, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(content_string.encode("utf-8")).hexdigest()
