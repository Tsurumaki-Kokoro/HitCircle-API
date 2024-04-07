from typing import Dict, Any

import httpx
from loguru import logger

from app.network.network import httpx_request
from app.network.public_token import PublicToken
from app.osu_utils.file import cache_dir
from app.user.models import UserModel


class OsuUser:
    def __init__(self):
        self.token_client = PublicToken()

    async def get_user_uid(self, osu_username: str) -> Dict[str, Any]:
        max_retries = 2  # 设置最大重试次数，防止无限循环
        for _ in range(max_retries):
            token = await self.token_client.get_public_token()
            url = f"https://osu.ppy.sh/api/v2/users/{osu_username}/osu"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            }

            try:
                response = await httpx_request("GET", url, headers=headers)
                return response["id"]  # 直接在成功时返回
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise Exception("User not found")
                elif e.response.status_code == 401:
                    await self.token_client.set_public_token()
                    logger.warning("Token refreshed, retrying...")
                    continue  # Token 已刷新，进行下一次循环重试
                else:
                    raise

        raise Exception("Maximum retry attempts reached, check your token or network connection")


def game_mode_int_to_string(game_mode: int) -> str:
    """
    将 osu! 游戏模式的整数转换为字符串
    :param game_mode:
    :return:
    """
    return {
        0: "osu",
        1: "taiko",
        2: "fruits",
        3: "mania"
    }.get(game_mode, "osu")


async def download_user_avatar(avatar_url: str) -> bytes:
    """
    下载用户头像
    :param avatar_url:
    :return:
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(avatar_url)
    return response.content


async def get_user_avatar(uid: int, avatar_url: str) -> bytes:
    """
    获取用户头像
    :param uid:
    :param avatar_url:
    :return:
    """
    path = cache_dir / "user" / f"{uid}"
    file_affix = avatar_url.split(".")[-1]
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    file_name = f"{uid}.{file_affix}"
    if (path / file_name).exists():
        with open((path / file_name), "rb") as f:
            content = f.read()
    else:
        with open((path / file_name), "wb") as f:
            file = await download_user_avatar(avatar_url)
            f.write(file)
            content = file
    return content


async def download_user_badge(img_url: str) -> bytes:
    """
    下载用户徽章
    :param img_url:
    :return:
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(img_url)
    return response.content


async def get_user_badge(uid: int, img_url: str, description: str) -> bytes:
    """
    获取用户徽章
    :param uid:
    :param img_url:
    :param description:
    :return:
    """
    path = cache_dir / "user" / f"{uid}"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    file_name = f"{description}.png"
    if (path / file_name).exists():
        with open((path / file_name), "rb") as f:
            content = f.read()
    else:
        with open((path / file_name), "wb") as f:
            file = await download_user_badge(img_url)
            f.write(file)
            content = file
    return content


async def get_redirected_bg():
    """
    获取重定向后的背景图片
    :return:
    """
    async with httpx.AsyncClient() as client:
        # 禁止自动跟随重定向
        response = await client.get("https://api.gumengya.com/Api/DmImg?format=image", follow_redirects=False)

        # 检查响应状态码，看是否是重定向
        if response.status_code in (301, 302, 303, 307, 308):
            # 获取重定向的 URL
            redirect_url = response.headers.get("Location")

            # 根据重定向的 URL 发起新的请求
            redirected_response = await client.get(redirect_url)

            # 返回重定向后的响应内容
            return redirected_response.content
        else:
            # 如果没有重定向，直接返回原始响应内容
            return response.content


async def get_info_bg(osu_uid: int) -> bytes:
    path = cache_dir / "user" / f"{osu_uid}"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    file_name = "info.png"
    if (path / file_name).exists():
        with open((path / file_name), "rb") as f:
            content = f.read()
    else:
        content = await get_redirected_bg()

    return content


async def get_all_bound_users() -> list:
    """
    获取所有绑定用户
    :return:
    """
    unique_osu_uid = await UserModel.all().distinct().values_list("osu_uid", flat=True)
    return list(set(unique_osu_uid))
