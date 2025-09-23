import hashlib
import json

from wagtail.models import Page


def get_page_seo_metadata(instance: Page) -> dict[str, str | list[str]]:
    """Extract SEO metadata from a Page instance"""
    meta_keywords: list[str] = []
    if hasattr(instance, "meta_keywords") and instance.meta_keywords:
        meta_keywords = [
            keyword.strip()
            for keyword in instance.meta_keywords.split(",")
            if keyword.strip()
        ]
    tags: list[str] = []
    if hasattr(instance, "tags") and instance.tags:
        tags = [tag.name for tag in instance.tags.all()]
    return {
        "seo_title": instance.seo_title or instance.title,
        "search_description": getattr(instance, "search_description", "") or "",
        "meta_keywords": meta_keywords,
        "tags": tags,
    }


def get_page_hash(page: Page) -> str:
    """Generate page hash for tracking changes"""
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
