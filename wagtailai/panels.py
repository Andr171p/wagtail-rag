from typing import Any, ClassVar, TypedDict, TypeVar, cast, override

from collections.abc import Callable, Sequence

from html_to_markdown import convert_to_markdown
from wagtail.admin.panels import Panel
from wagtail.blocks import StreamValue
from wagtail.models import Page
from wagtail.rich_text import RichText

from .utils import convert_stream_field_to_markdown, get_page_seo_metadata

type ContentProcessor = Callable[[Any], str]
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


class RAGIndexableData(TypedDict):
    id: int
    url: str
    slug: str
    title: str
    seo_metadata: dict[str, str | list[str]]
    content: str
    last_published_at: str


class RAGFieldPanel(Panel):
    """Panel for manage AI indexing"""
    def __init__(
            self,
            field_name: str = "rag_field",
            processor: ContentProcessor | None = None,
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
        if self.field_name == "title":
            value = f"# {value}"
        elif isinstance(value, RichText):
            value = convert_to_markdown(value.source)
        elif isinstance(value, StreamValue):
            value = convert_stream_field_to_markdown(value)
        elif hasattr(value, "all"):
            items: list[str] = [str(item) for item in value.all()]
            value = ", ".join(items)
        else:
            value = convert_to_markdown(value)
        return str(value) if value else ""


class MetaRAGFieldPanel(RAGFieldPanel):
    """Special panel for page metadata"""
    def __init__(self, meta_field: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.meta_field = meta_field

    @override
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


class RAGPanelCollection(Panel):
    def __init__(self, panels: Sequence[Panel], include_meta: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.panels = list(panels)
        if include_meta:
            self.panels.extend(self.default_meta_panels)

    def get_markdown_content(self, instance: Page) -> str:
        """Generate Markdown content from RAG panels"""
        content_parts: list[str] = []
        for panel in self.panels:
            if isinstance(panel, RAGFieldPanel):
                value = panel.get_value(instance)
                if value and value.strip():
                    if panel.heading:
                        content_parts.append(f"## META: {panel.heading}")
                    content_parts.append(value)
        return "\n\n".join(content_parts)

    def get_rag_indexable_data(self, instance: Page) -> RAGIndexableData:
        return {
            "id": instance.id,
            "url": instance.get_full_url() or "",
            "slug": instance.slug,
            "title": instance.title,
            "seo_metadata": get_page_seo_metadata(instance),
            "content": self.get_markdown_content(instance),
            "last_published_at": instance.last_published_at.isoformat(),
        }

    @property
    def default_meta_panels(self) -> list[MetaRAGFieldPanel]:
        return [
            MetaRAGFieldPanel(meta_field="title", heading="Page Title"),
            MetaRAGFieldPanel(meta_field="seo_title", heading="SEO Title"),
            MetaRAGFieldPanel(meta_field="search_description", heading="Meta Description"),
            MetaRAGFieldPanel(meta_field="meta_keywords", heading="Meta Keywords"),
            MetaRAGFieldPanel(meta_field="url", heading="Page URL"),
            MetaRAGFieldPanel(meta_field="slug", heading="Page Slug"),
            MetaRAGFieldPanel(meta_field="last_published_at", heading="Last Updated"),
        ]


class RAGIndexableMixin:
    rag_panels: ClassVar[list[RAGFieldPanel]] = []
    include_meta_fields: ClassVar[bool] = True

    @property
    def rag_panel_collection(self) -> RAGPanelCollection:
        return RAGPanelCollection(self.rag_panels, self.include_meta_fields)

    def get_markdown_content(self: Page) -> str:
        return self.rag_panel_collection.get_markdown_content(self)

    def get_rag_fields(self) -> list[str]:
        fields: list[str] = [
            panel.field_name for panel in self.rag_panels if isinstance(panel, RAGFieldPanel)
        ]
        if self.include_meta_fields:
            fields.extend(META_FIELDS)
        return fields

    def get_rag_indexable_data(self: Page) -> RAGIndexableData:
        return self.rag_panel_collection.get_rag_indexable_data(self)


def register_rag_indexable[PageSubclass: type[Page]](
        *panels: RAGFieldPanel | PageSubclass, include_meta: bool = True
) -> Callable[[PageSubclass], PageSubclass] | PageSubclass:
    """Декоратор для добавления индексации полей страницы для AI-ассистента"""
    if len(panels) == 1 and isinstance(panels[0], type) and issubclass(panels[0], Page):
        return cast(PageSubclass, panels[0])

    def decorator(cls: PageSubclass) -> PageSubclass:
        if not issubclass(cls, Page):
            raise TypeError("RAG-indexable class must be a subclass of Page!")
        cls.rag_panels = list(panels)
        cls.include_meta_fields = include_meta

        @property
        def rag_panel_collection(self) -> RAGPanelCollection:
            return RAGPanelCollection(self.rag_panels, self.include_meta_fields)

        def get_markdown_content(self) -> str:
            return self.rag_panel_colllection.get_markdown_content(self)

        def get_rag_fields(self) -> list[str]:
            fields: list[str] = [rag_panel.field_name for rag_panel in self.rag_panels]
            if self.include_meta_fields:
                fields.extend(META_FIELDS)
            return fields

        def get_rag_indexable_data(self) -> RAGIndexableData:
            return self.rag_panel_collection.get_rag_indexable_data(self)

        cls.rag_panel_collection = rag_panel_collection
        cls.get_markdown_content = get_markdown_content
        cls.get_rag_fields = get_rag_fields
        cls.get_rag_indexable_data = get_rag_indexable_data
        return cls
    return decorator
