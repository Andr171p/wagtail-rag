import logging

from django.dispatch import receiver
from wagtail.models import Page, Revision
from wagtail.signals import page_published

logger = logging.getLogger(__name__)


@receiver(page_published)
def page_published_handler(
        sender: Page, instance: Page, revision: Revision, **kwargs  # noqa: ARG001
) -> None:
    try:
        if not hasattr(instance, "get_rag_indexable_data"):
            logger.debug("Page %s does not support RAG indexing!", instance.id)
            return
        rag_indexable_data = instance.get_rag_indexable_data()
        rag_fields = instance.get_rag_fields()
        print(rag_indexable_data)  # noqa: T201
        logger.info("RAG indexing page: %s (ID %s)", instance.title, instance.id)
        logger.info("RAG fields detected: %s", rag_fields)
        logger.info("Content length: %s characters", len(rag_indexable_data["content"]))
    except Exception:
        logger.exception("Error occurred while handle page_published, error: {e}")
