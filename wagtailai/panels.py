from typing import Any, ClassVar, TypeAlias

from collections.abc import Callable, Sequence

from wagtail.admin.panels import Panel
from wagtail.models import Page
from wagtail.rich_text import RichText

ProcessorFunc: TypeAlias = Callable[[Any], str]


class AIPanel(Panel):
    """Panel for manage AI indexing"""
    def __init__(
            self,
            field_name: str = "ai_field",
            processor: ProcessorFunc | None = None,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.field_name = field_name
        self.processor = processor

    def get_value(self, instance: Page) -> str:
        value = getattr(instance, self.field_name, None)
        if callable(value):
            value = value()
        if self.processor:
            value = self.processor(value)
        if isinstance(value, RichText):
            value = value.source
        elif hasattr(value, "all"):
            items: list[str] = [str(item) for item in value.all()]
            value = ", ".join(items)
        return str(value) if value else ""


class AIPanelGroup(Panel):
    """Group of AI panels"""
    def __init__(self, panels: Sequence[Panel], **kwargs) -> None:
        super().__init__(**kwargs)
        self.panels = panels

    def get_ai_content(self, instance: Page) -> str:
        """Generate content using all AI panels"""
        content: list[str] = []
        for panel in self.panels:
            if isinstance(panel, AIPanel):
                value = panel.get_value(instance)
                if value:
                    content.append(value)
        return "\n\n".join(content)


class AIIndexablePageMixin:
    ai_panels: ClassVar[list[AIPanel]] = []

    @property
    def ai_panel_group(self) -> AIPanelGroup:
        return AIPanelGroup(self.ai_panels)

    def get_ai_content(self: Page) -> str:
        return self.ai_panel_group.get_ai_content(self)

    def get_ai_fields(self) -> list[str]:
        return [panel.field_name for panel in self.ai_panels if isinstance(panel, AIPanel)]
