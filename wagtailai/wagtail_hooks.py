from typing import ClassVar

from wagtail import hooks
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.model import ModelViewSet

from .models import RAGSettings


class RAGSettingsViewSet(ModelViewSet):
    model = RAGSettings
    icon = "cog"
    menu_label = "RAG Settings"
    menu_name = "rag-settings"
    add_to_settings_menu = True
    list_display: ClassVar[list[str]] = ["base_url", "timeout", "api_version", "is_active"]
    form_fields: ClassVar[list[str]] = ["base_url", "timeout", "api_version", "is_active"]


rag_settings_viewset = RAGSettingsViewSet("rag-settings")


@hooks.register("register_admin_viewset")
def register_rag_settings_viewset() -> RAGSettingsViewSet:
    return rag_settings_viewset
