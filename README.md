```python
from django.db import models
from wagtail.models import Page
from wagtailai.panels import AIPanel, ai_indexable


@ai_indexable(AIPanel("body"), include_meta=True)
class MyPage(Page):
    body = models.TextField(max_length=500)
```