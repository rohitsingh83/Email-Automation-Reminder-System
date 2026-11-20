"""Open and click tracking helpers for email campaigns."""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, Response

router = APIRouter()
PIXEL_GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


@router.get("/t/o/{message_id}.gif")
def track_open(message_id: str):
    return Response(content=PIXEL_GIF, media_type="image/gif")


@router.get("/t/c/{message_id}")
def track_click(message_id: str, url: str = "https://example.com"):
    return RedirectResponse(url=url)
