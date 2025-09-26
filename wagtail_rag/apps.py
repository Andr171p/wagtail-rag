from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class WagtailRAGConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_rag"
    verbose_name = _("Wagtail RAG")

    def ready(self) -> None:  # noqa: PLR6301
        setattr(settings, "WAGTAILAI_RAG_BASE_URL")
        import wagtail_rag.signals  # noqa: PLC0415
