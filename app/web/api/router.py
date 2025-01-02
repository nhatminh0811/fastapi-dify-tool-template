from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

from app.repositories.generate_text import generate_text
from app.schemas.request_schema import GenerateTextRequest
from app.utils.api_utils import make_response
from app.web.api import echo, monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])


@api_router.post("/generate_text")
async def generate_text(request: GenerateTextRequest) -> StreamingResponse:
    """Test generator text response."""

    text = request.input_text
    generated_text = generate_text(text)
    return make_response(content=generated_text)
