from fastapi import APIRouter, HTTPException, Response, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from loguru import logger

from app.config.settings import osu_api
from app.security.api_key import get_api_key
from app.osu_utils.beatmap import get_map_bg, get_osu_file_path, get_bg_filename, get_info_img

beatmap_router = APIRouter(tags=["Beatmap & BeatmapSet"])
limiter = Limiter(key_func=get_remote_address)


@beatmap_router.get("/beatmap/cover", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
@limiter.limit("20/minute")
async def get_beatmap_cover(request: Request, beatmap_id: int = None, beatmapset_id: int = None):
    try:
        if not beatmap_id and not beatmapset_id:
            raise HTTPException(status_code=400, detail="Bad request")
        if beatmap_id:
            beatmap_set_info = osu_api.beatmapset(beatmap_id=beatmap_id)
        else:
            beatmap_set_info = osu_api.beatmapset(beatmapset_id=beatmapset_id)

        if not beatmap_id:
            beatmap_id = beatmap_set_info.beatmaps[0].id
        else:
            beatmap_id = beatmap_id
        osu_file_path = await get_osu_file_path(
            beatmap_set_info.id, beatmap_id
        )
        bg_name = get_bg_filename(osu_file_path)

    except Exception as e:
        logger.error(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    content = await get_map_bg(map_id=beatmap_set_info.beatmaps[0].id, set_id=beatmap_set_info.id, bg_name=bg_name)

    return Response(content=content, media_type="image/jpeg")


@beatmap_router.get("/beatmap/info", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
@limiter.limit("20/minute")
async def get_beatmap_info(request: Request, beatmap_id: int = None, beatmapset_id: int = None,
                           theme: str = "default"):
    """
    获取 beatmap 信息图片, 传入 beatmap_id 或 beatmapset_id
    """
    return await get_info_img(beatmap_id, beatmapset_id, theme)
