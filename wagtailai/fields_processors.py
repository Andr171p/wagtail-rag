from html_to_markdown import convert_to_markdown
from wagtail.fields import StreamField


def process_stream_field(stream_field: StreamField) -> str:
    """Process StreamField to Markdown format"""
    serialized_fields: list[dict[str, str]] = stream_field.stream_data
    return "\n\n".join([
        convert_to_markdown(serialized_field["value"])
        for serialized_field in serialized_fields
    ])
