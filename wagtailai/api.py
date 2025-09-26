from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import BaseAPIViewSet

BAD_REQUEST_STATUS_CODE = 400


class RAGViewsSet(BaseAPIViewSet):
    @action(detail=False, methods=["POST"], url_path="rag")
    def ask_assistant(self, request: Request) -> Response:
        text = request.data.get("text", "").strip()
        session_id = request.data.get("session_id")
        if not text:
            return Response(
                {"error": "Text of message is required"}, status=BAD_REQUEST_STATUS_CODE
            )
        ...
        return ...
