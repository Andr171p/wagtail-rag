from django.dispatch import receiver
from wagtail.models import Page, Revision
from wagtail.signals import page_published


@receiver(page_published)
def page_published_handler(sender: Page, instance: Page, revision: Revision, **kwargs) -> None:
    """Обработка события - публикации страницы"""
    ...
