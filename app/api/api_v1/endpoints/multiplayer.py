import enum

from fastapi import APIRouter, HTTPException, Response, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.security.api_key import get_api_key
from app.osu_utils.multiplayer import generate_match_history_img, generate_rating_img

multiplayer_router = APIRouter(tags=["Multiplayer"])
limiter = Limiter(key_func=get_remote_address)


class SupportedAlgorithm(str, enum.Enum):
    OSU_PLUS = "osuplus"
    BATH_BOT = "bathbot"
    FLASHLIGHT = "flashlight"


@multiplayer_router.get("/multiplayer/history", responses={
    200: {"description": "OK", "content": {"image/jpeg": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "No match found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_match_history_img(request: Request, mp_id: int = None, theme: str = "default"):
    return await generate_match_history_img(mp_id, theme)


@multiplayer_router.get("/multiplayer/rating", responses={
    200: {"description": "OK", "content": {"image/jpeg": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "No match found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_rating_img(request: Request, algorithm: SupportedAlgorithm,  mp_id: int = None, theme: str = "default"):
    return await generate_rating_img(mp_id, algorithm.value, theme)
