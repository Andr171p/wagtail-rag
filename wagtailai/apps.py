from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class WagtailAIConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtailai"
    verbose_name = _("Wagtail AI")

    def ready(self) -> None:  # noqa: PLR6301
        setattr(settings, "WAGTAILAI_RAG_BASE_URL")
        import wagtailai.signals  # noqa: PLC0415
