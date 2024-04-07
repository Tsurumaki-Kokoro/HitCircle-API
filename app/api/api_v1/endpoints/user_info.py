from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.security.api_key import get_api_key
from app.osu_utils.user_info import generate_player_info_img

info_router = APIRouter(tags=["Player Info"])
limiter = Limiter(key_func=get_remote_address)


@info_router.get("/user_info", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_user_info(request: Request, platform: str, platform_uid: int, game_mode: int = None,
                        compare_with: int = None):
    return await generate_player_info_img(platform, platform_uid, game_mode, compare_with)
