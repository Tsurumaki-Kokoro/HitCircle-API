import json

from fastapi import APIRouter, Depends, File, UploadFile, Form
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.api.api_v1.schemas.user_info import UserInfoUpdateSchema
from app.osu_utils.user_info import (generate_player_info_img, update_user_info_background,
                                     generate_player_pp_control_result, generate_player_pp_analyze_img)
from app.security.api_key import get_api_key

info_router = APIRouter(tags=["Player Info"])
limiter = Limiter(key_func=get_remote_address)


@info_router.get("/user_info", responses={
    200: {"description": "OK", "content": {"image/png": {}}},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_user_info(request: Request, platform: str, platform_uid: str, game_mode: int = None, user_name: str = None,
                        compare_with: int = None):
    return await generate_player_info_img(platform, platform_uid, game_mode, user_name, compare_with)


@info_router.post("/user_info/update_background", responses={
    200: {"description": "OK"},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def update_background(request: Request, data: str = Form(...), background_file: UploadFile = File(...)):
    data_dict = json.loads(data)  # 解析 JSON 字符串
    data = UserInfoUpdateSchema(**data_dict)  # 验证并创建数据模型实例
    return await update_user_info_background(data.platform, data.platform_uid, background_file)


@info_router.get("/user_info/extra/performance_control", responses={
    200: {"description": "OK"},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_performance_control_result(request: Request, platform: str, platform_uid: str, pp: float):
    return await generate_player_pp_control_result(platform, platform_uid, pp)


@info_router.get("/user_info/extra/performance_analyze", responses={
    200: {"description": "OK"},
    400: {"description": "Bad request"},
    403: {"description": "Access Token required or invalid"},
    404: {"description": "User not found"},
    500: {"description": "Internal server error"}
}, dependencies=[Depends(get_api_key)])
async def get_performance_analyze_result(request: Request, platform: str, platform_uid: str, theme: str = 'default'):
    return await generate_player_pp_analyze_img(platform, platform_uid, theme)
