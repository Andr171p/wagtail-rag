from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailAIConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtailai"
    verbose_name = _("Wagtail AI")

    def ready(self) -> None:
        import wagtailai.signals
