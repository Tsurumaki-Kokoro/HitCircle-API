import shutil

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.security.api_key import get_api_key
from app.osu_utils.file import cache_dir, log_dir
from app.osu_utils.user import get_all_bound_users
from app.osu_utils.user_info import save_user_info
from loguru import logger

task_router = APIRouter(tags=["Task"])
limiter = Limiter(key_func=get_remote_address)


@task_router.post("/task/clear_cache", responses={
    200: {"description": "OK"},
    403: {"description": "Access Token required or invalid"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def clear_cache(request: Request):
    """
    清除缓存
    """
    beatmap_cache_dir = cache_dir / "beatmap" / "osu_file"
    user_cache_dir = cache_dir / "user"
    try:
        # Clear beatmap cache
        if beatmap_cache_dir.exists():
            for dirs in beatmap_cache_dir.iterdir():
                if dirs.is_dir():
                    shutil.rmtree(dirs)  # 使用 shutil.rmtree 删除目录及其所有内容

        # Clear user cache
        if user_cache_dir.exists():
            for user_dir in user_cache_dir.iterdir():
                if user_dir.is_dir():
                    # 删除与子目录名称相同的文件（不考虑后缀）
                    for file in user_dir.iterdir():
                        if file.is_file() and file.stem == user_dir.name:
                            file.unlink()  # 删除文件
                    # 检查目录是否为空，若为空则删除该目录
                    if not any(user_dir.iterdir()):
                        user_dir.rmdir()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Cache cleared"}


@task_router.post("/task/pack_logs", responses={
    200: {"description": "OK", "content": {"application/octet-stream": {}}},
    403: {"description": "Access Token required or invalid"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def pack_logs(request: Request):
    """
    打包日志文件, 并返回下载链接
    """
    try:
        file_path = log_dir
        shutil.make_archive(file_path, "zip", log_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(file_path.with_suffix(".zip"), filename="logs.zip")


@task_router.post("/task/update_user_info", responses={
    200: {"description": "OK"},
    403: {"description": "Access Token required or invalid"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def update_user_info(request: Request):
    users = await get_all_bound_users()
    try:
        for user in users:
            logger.info(f"Updating user info for {user}")
            for game_mode in range(4):
                await save_user_info(user, game_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "User info updated"}
