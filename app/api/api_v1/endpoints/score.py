from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.security.api_key import get_api_key
from app.osu_utils.score import generate_play_record_img, generate_user_score_img

score_router = APIRouter(tags=["Score"])
limiter = Limiter(key_func=get_remote_address)


@score_router.get("/score/recent_play", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found or No recent play record found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_recent_play_img(request: Request, platform: str, platform_uid: str, game_mode: int = None,
                              include_fails: bool = False, theme: str = "default"):
    return await generate_play_record_img(platform, platform_uid, "recent", game_mode, include_fails, theme)


@score_router.get("/score/best_play", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found or No best play record found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_best_play_img(request: Request, platform: str, platform_uid: str, best_index: int = 1,
                            game_mode: int = None, theme: str = "default"):
    return await generate_play_record_img(platform, platform_uid, "best", game_mode, False, theme, best_index)


@score_router.get("/score/user_score", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_user_score_img(request: Request, platform: str, platform_uid: str, beatmap_id: int, mods: str = None,
                             theme: str = "default"):
    return await generate_user_score_img(platform, platform_uid, beatmap_id, mods, theme)
