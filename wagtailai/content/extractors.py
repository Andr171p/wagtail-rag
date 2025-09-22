from typing import Any

from django.conf import settings
from wagtail.models import Page
import re
from html.parser import HTMLParser

from .exceptions import ContentExtractionError


class HTMLTextExtractor(HTMLParser):
    """Парсер для извлечения чистого текста из HTML"""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_tags = {'script', 'style', 'nav', 'footer', 'header'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
        if tag.lower() in ['p', 'br', 'div']:
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        self.current_tag = None
        if tag.lower() in ['p', 'div', 'li']:
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            cleaned_data = data.strip()
            if cleaned_data:
                self.text_parts.append(cleaned_data)

    def get_text(self):
        return ' '.join(self.text_parts).strip()


class ContentExtractor:
    def __init__(self):
        self.html_parser = HTMLTextExtractor()

    def extract_page_content(self, page: Page) -> dict[str, Any]:
        """Извлекает структурированный контент из страницы"""
        try:
            content = {
                'id': page.id,
                'title': page.title,
                'url': page.full_url,
                'type': self._get_page_type(page),
                'language': self._get_page_language(page),
                'metadata': self._extract_metadata(page),
                'content': self._extract_main_content(page),
                'sections': self._extract_sections(page),
                'last_updated': self._get_last_updated(page),
                'tags': self._extract_tags(page),
                'categories': self._extract_categories(page),
            }

            # Очищаем None значения
            content = {k: v for k, v in content.items() if v is not None}

            return content

        except Exception as e:
            raise ContentExtractionError(f"Failed to extract content: {str(e)}")

    def _get_page_type(self, page: Page) -> str:
        """Определяем тип страницы"""
        return page.specific_class.__name__.lower()

    def _get_page_language(self, page: Page) -> str:
        """Получаем язык страницы"""
        if hasattr(page, 'locale'):
            return page.locale.language_code
        return getattr(settings, 'LANGUAGE_CODE', 'en')

    def _get_last_updated(self, page: Page) -> str:
        """Получаем дату последнего обновления"""
        if page.last_published_at:
            return page.last_published_at.isoformat()
        return None

    def _extract_metadata(self, page: Page) -> dict[str, Any]:
        """Извлекаем метаданные страницы"""
        metadata = {
            'search_description': page.search_description,
            'seo_title': getattr(page, 'seo_title', None),
            'slug': page.slug,
            'depth': page.depth,
        }

        # Добавляем custom metadata если есть
        if hasattr(page, 'metadata'):
            metadata.update(page.metadata)

        return {k: v for k, v in metadata.items() if v}

    def _extract_main_content(self, page: Page) -> str:
        """Извлекаем основной контент страницы"""
        content_parts = []

        # Пробуем разные методы извлечения контента
        methods = [
            self._extract_from_searchable_content,
            self._extract_from_body_field,
            self._extract_from_streamfield,
            self._extract_from_richtext,
        ]

        for method in methods:
            content = method(page)
            if content:
                content_parts.append(content)

        # Если ничего не нашли, используем поисковое описание
        if not content_parts and page.search_description:
            content_parts.append(page.search_description)

        return '\n\n'.join(content_parts).strip()

    def _extract_from_searchable_content(self, page: Page) -> str:
        """Извлекаем контент через поисковый индекс"""
        try:
            if hasattr(page, 'get_searchable_content'):
                content = page.get_searchable_content()
                return ' '.join(content).strip()
        except Exception:
            pass
        return None

    def _extract_from_body_field(self, page: Page) -> str:
        """Извлекаем контент из поля body"""
        if hasattr(page, 'body') and page.body:
            return self._clean_html_content(str(page.body))
        return None

    def _extract_from_streamfield(self, page: Page) -> str:
        """Извлекаем контент из StreamField"""
        content_parts = []

        if hasattr(page, 'body') and isinstance(page.body, list):
            for block in page.body:
                if hasattr(block, 'value'):
                    block_content = self._extract_block_content(block.value)
                    if block_content:
                        content_parts.append(block_content)

        return '\n'.join(content_parts) if content_parts else None

    def _extract_block_content(self, block_value) -> str:
        """Извлекаем контент из блока StreamField"""
        if isinstance(block_value, str):
            return self._clean_html_content(block_value)
        elif hasattr(block_value, 'source'):  # RichText
            return self._clean_html_content(block_value.source)
        elif isinstance(block_value, dict):
            # Рекурсивно обрабатываем словари
            text_parts = []
            for key, value in block_value.items():
                if isinstance(value, (str, int, float)):
                    text_parts.append(str(value))
                elif isinstance(value, dict):
                    text_parts.append(self._extract_block_content(value))
            return ' '.join(text_parts)
        elif isinstance(block_value, list):
            # Рекурсивно обрабатываем списки
            return ' '.join(self._extract_block_content(item) for item in block_value)

        return None

    def _extract_from_richtext(self, page: Page) -> str:
        """Извлекаем контент из RichText полей"""
        content_parts = []

        # Ищем все RichText поля
        for field_name in dir(page):
            field_value = getattr(page, field_name, None)
            if (field_value and hasattr(field_value, 'source') and
                    not field_name.startswith('_')):
                content_parts.append(self._clean_html_content(field_value.source))

        return '\n'.join(content_parts) if content_parts else None

    def _clean_html_content(self, html_content: str) -> str:
        """Очищаем HTML контент от тегов"""
        if not html_content:
            return ''

        try:
            self.html_parser = HTMLTextExtractor()
            self.html_parser.feed(html_content)
            return self.html_parser.get_text()
        except Exception:
            # Fallback: простой regex для удаления тегов
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            return clean_text.strip()

    def _extract_sections(self, page: Page) -> list[dict[str, Any]]:
        """Извлекаем структурированные секции контента"""
        sections = []

        # Пример: извлечение заголовков и связанного контента
        if hasattr(page, 'body') and page.body:
            current_section = None

            for block in page.body:
                if hasattr(block, 'block_type'):
                    if block.block_type == 'heading':
                        if current_section:
                            sections.append(current_section)
                        current_section = {
                            'title': self._clean_html_content(str(block.value)),
                            'content': '',
                            'type': 'section'
                        }
                    elif current_section and block.block_type in ['paragraph', 'text']:
                        current_section['content'] += self._clean_html_content(str(block.value)) + '\n'

            if current_section:
                sections.append(current_section)

        return sections if sections else None

    def _extract_tags(self, page: Page) -> list[str]:
        """Извлекаем теги страницы"""
        tags = []

        if hasattr(page, 'tags') and page.tags.all():
            tags = [tag.name for tag in page.tags.all()]

        return tags if tags else None

    def _extract_categories(self, page: Page) -> list[str]:
        """Извлекаем категории страницы"""
        categories = []

        # Поддержка популярных Wagtail пакетов для категорий
        if hasattr(page, 'categories') and page.categories.all():
            categories = [cat.name for cat in page.categories.all()]
        elif hasattr(page, 'category') and page.category:
            categories = [page.category.name]

        return categories if categories else None
