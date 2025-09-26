# Wagtailai

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![Wagtail](https://img.shields.io/badge/Wagtail-5.0+-blue.svg)](https://wagtail.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Установка

**pip**
```shell
pip install "git+https://github.com/Andr171p/wagtailai.git"
```

**poetry**
```shell
poetry add "git+https://github.com/Andr171p/wagtailai.git"
```

**uv**
```shell
uv add "git+https://github.com/Andr171p/wagtailai.git"
```

## Настройка в проекте
```python
# settings.py
INSTALLED_APPS = [
    # ... другие приложения
    "wagtailai",  # ваше приложение
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    # ... остальные приложения
]
```

## Пример индексации страницы

```python
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtailai.panels import RAGFieldPanel, register_rag_indexable


@register_rag_indexable(
    RAGFieldPanel("headline"),
    RAGFieldPanel("intro"),
    RAGFieldPanel("body"), 
    include_meta=True
)
class MyPage(Page):
    headline = models.CharField(max_length=100)
    intro = RichTextField(max_length=250)
    body = RichTextField()
    # SEO metadata
    search_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("headline"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]
```