from wagtail.models import Page


def extract_page_content(page: Page) -> ...:
    return {
        "id": page.id,
        "url": page.url,
        "title": page.title,
        "seo_title": page.seo_title,
        "search_description": page.search_description,
        "depth": page.depth,
    }
