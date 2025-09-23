# Wagtailai

## Пример индексации страницы

```python
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtailai.panels import AIPanel, ai_indexable


@ai_indexable(
    AIPanel("headline"),
    AIPanel("intro"),
    AIPanel("body"), 
    include_meta=True
)
class MyPage(Page):
    headline = models.CharField(max_length=100)
    intro = RichTextField(max_length=250)
    body = RichTextField()
    # SEO metadata
    search_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
```