from typing import Self

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


@register_setting
class RAGSettings(BaseSiteSetting):
    base_url = models.URLField(
        default="http://localhost:8000",
        verbose_name=_("URL адрес RAG сервиса"),
    )
    timeout = models.PositiveIntegerField(
        default=30, verbose_name=_("Таймаут для ожидания ответа")
    )
    api_version = models.CharField(
        max_length=10, default="v1", verbose_name=_("Версия API"),
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Включить/выключить RAG сервис"),
    )

    def __str__(self) -> str:
        return "RAG Settings"

    class Meta:
        verbose_name = _("RAG настройки")
        verbose_name_plural = _("RAG настройки")

    def save(self, *args, **kwargs) -> None:
        """Allow only one record of settings"""
        if not self.pk and RAGSettings.objects.exists():
            raise ValidationError("Only one RAG Settings instance allowed")
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> Self:
        from wagtail.models import Site  # noqa: PLC0415

        site = Site.objects.get(is_default_site=True)
        return cls.for_site(site)
