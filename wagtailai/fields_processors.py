from html_to_markdown import convert_to_markdown
from wagtail.blocks import StreamValue
from wagtail.fields import StreamField

# def process_stream_field(stream_field: StreamField) -> str:
#    """Process StreamField to Markdown format"""
#    serialized_fields: list[dict[str, str]] = stream_field.stream_data  # noqa: ERA001
#    return "\n\n".join([
#        convert_to_markdown(serialized_field["value"])  # noqa: ERA001
#        for serialized_field in serialized_fields
#    ])  # noqa: ERA001, RUF100


def process_stream_field(stream_field: StreamValue) -> str:
    parts: list[str] = []
    for block in stream_field:
        block_value = block.value
        if hasattr(block_value, "source") and isinstance(block_value.source, str):
            parts.append(convert_to_markdown(block_value.source))
        elif isinstance(block_value, dict):
            block_content: list[...] = []
            for key, value in block_value.items():
                if isinstance(value, str):
                    block_content.append(f"**{key}**: {value}")
                elif hasattr(value, "source"):
                    block_content.append(f"**{key}**: {convert_to_markdown(value.source)}")
            if block_content:
                parts.append("\n".join(block_content))
        elif isinstance(block_value, str):
            parts.append(block_value)
    return "\n\n".join(parts)
