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
        if not hasattr(instance, "to_ai_json"):
            logger.debug("Page %s does not support AI indexing!", instance.id)
            return
        ai_json = instance.to_ai_json()
        ai_fields = instance.get_ai_fields()
        print(ai_json)
        logger.info("AI indexing page: %s (ID %s)", instance.title, instance.id)
        logger.info("AI fields detected: %s", ai_fields)
        logger.info("Content length: %s characters", len(ai_json["content"]))
    except Exception:
        logger.exception("Error occurred while handle page_published, error: {e}")
