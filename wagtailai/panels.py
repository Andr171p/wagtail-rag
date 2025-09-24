from typing import Any, ClassVar, TypedDict, TypeVar, cast

from collections.abc import Callable, Sequence

from html_to_markdown import convert_to_markdown
from wagtail.admin.panels import Panel
from wagtail.blocks import StreamValue
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.rich_text import RichText

from .fields_processors import process_stream_field
from .utils import get_page_seo_metadata

type ProcessorFunc = Callable[[Any], str]
PageType = TypeVar("PageType", bound=Page)
PageSubclass = TypeVar("PageSubclass", bound=type[Page])

META_FIELDS: list[str] = [
    "id",
    "title",
    "seo_title",
    "search_description",
    "meta_keywords",
    "url",
    "slug",
    "last_published_at",
]


class AIPageJSON(TypedDict):
    id: int
    url: str
    slug: str
    title: str
    seo_metadata: dict[str, str | list[str]]
    content: str
    last_published_at: str


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
            value = convert_to_markdown(value.source)
        elif isinstance(value, StreamValue):
            print("Обработка StreamField")
            value = process_stream_field(value)
        elif hasattr(value, "all"):
            items: list[str] = [str(item) for item in value.all()]
            value = ", ".join(items)
        else:
            value = convert_to_markdown(value)
        return str(value) if value else ""


class MetaAIPanel(AIPanel):
    """Special panel for page metadata"""
    def __init__(self, meta_field: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.meta_field = meta_field

    def get_value(self, instance: Page) -> str:
        """Handling special meta-fields"""
        match self.meta_field:
            case "id":
                return str(instance.id)
            case "url":
                return instance.get_full_url()
            case "title":
                return instance.title
            case "seo_title":
                return getattr(instance, self.meta_field, "") or instance.title
            case "search_description":
                return getattr(instance, self.meta_field, "") or ""
            case "meta_keywords":
                return getattr(instance, self.meta_field, "") or ""
            case "slug":
                return instance.slug or ""
            case "last_published_at":
                return instance.last_published_at.isoformat() if instance.last_published_at else ""
        return super().get_value(instance)


class AIPanelGroup(Panel):
    """Group of AI panels"""
    def __init__(self, panels: Sequence[Panel], include_meta: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.panels = list(panels)
        if include_meta:
            self.panels.extend(self.default_meta_panels)

    def generate_ai_content_markdown(self, instance: Page) -> str:
        """Generate Markdown content from AI panels"""
        ai_content_parts: list[str] = []
        for panel in self.panels:
            if isinstance(panel, AIPanel):
                value = panel.get_value(instance)
                if value and value.strip():
                    if panel.heading:
                        ai_content_parts.append(f"## {panel.heading}")
                    ai_content_parts.append(value)
        return "\n\n".join(ai_content_parts)

    def to_ai_json(self, instance: Page) -> AIPageJSON:
        return {
            "id": instance.id,
            "url": instance.get_full_url() or "",
            "slug": instance.slug,
            "title": instance.title,
            "seo_metadata": get_page_seo_metadata(instance),
            "content": self.generate_ai_content_markdown(instance),
            "last_published_at": instance.last_published_at.isoformat(),
        }

    @property
    def default_meta_panels(self) -> list[MetaAIPanel]:
        return [
            MetaAIPanel(meta_field="title", heading="Page Title"),
            MetaAIPanel(meta_field="seo_title", heading="SEO Title"),
            MetaAIPanel(meta_field="search_description", heading="Meta Description"),
            MetaAIPanel(meta_field="meta_keywords", heading="Meta Keywords"),
            MetaAIPanel(meta_field="url", heading="Page URL"),
            MetaAIPanel(meta_field="slug", heading="Page Slug"),
            MetaAIPanel(meta_field="last_published_at", heading="Last Updated"),
        ]

    def get_ai_content(self, instance: Page) -> str:
        """Generate content using all AI panels"""
        content: list[str] = []
        for panel in self.panels:
            if isinstance(panel, (AIPanel, MetaAIPanel)):
                value = panel.get_value(instance)
                if value and value.strip():
                    if isinstance(panel, MetaAIPanel):
                        content.append(f"[META] {panel.heading or panel.meta_field}]: {value}")
                    else:
                        content.append(value)
        return "\n\n".join(content)


class AIIndexablePageMixin:
    ai_panels: ClassVar[list[AIPanel]] = []
    include_meta_fields: ClassVar[bool] = True

    @property
    def ai_panel_group(self) -> AIPanelGroup:
        return AIPanelGroup(self.ai_panels)

    def get_ai_content(self: Page) -> str:
        return self.ai_panel_group.get_ai_content(self)

    def get_ai_fields(self) -> list[str]:
        fields: list[str] = [
            panel.field_name for panel in self.ai_panels if isinstance(panel, AIPanel)
        ]
        if self.include_meta_fields:
            fields.extend(META_FIELDS)
        return fields

    def to_ai_json(self: Page) -> AIPageJSON:
        return self.ai_panel_group.to_ai_json(self)


def ai_indexable[PageSubclass: type[Page]](
        *panels: AIPanel | PageSubclass, include_meta: bool = True
) -> Callable[[PageSubclass], PageSubclass] | PageSubclass:
    """Декоратор для добавления индексации полей страницы для AI-ассистента"""
    if len(panels) == 1 and isinstance(panels[0], type) and issubclass(panels[0], Page):
        return cast(PageSubclass, panels[0])

    def decorator(cls: PageSubclass) -> PageSubclass:
        if not issubclass(cls, Page):
            raise TypeError("AI-indexable class must be a subclass of Page!")
        cls.ai_panels = list(panels)
        cls.include_meta_fields = include_meta

        @property
        def ai_panel_group(self) -> AIPanelGroup:
            return AIPanelGroup(self.ai_panels)

        def get_ai_content(self) -> str:
            return self.ai_panel_group.get_ai_content(self)

        def get_ai_fields(self) -> list[str]:
            fields: list[str] = [ai_panel.field_name for ai_panel in self.ai_panels]
            if self.include_meta_fields:
                fields.extend(META_FIELDS)
            return fields

        def to_ai_json(self) -> AIPageJSON:
            return self.ai_panel_group.to_ai_json(self)

        cls.ai_panel_group = ai_panel_group
        cls.get_ai_content = get_ai_content
        cls.get_ai_fields = get_ai_fields
        cls.to_ai_json = to_ai_json
        return cls
    return decorator
