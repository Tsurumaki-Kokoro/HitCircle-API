import asyncio
import re
import random
from io import BytesIO, TextIOWrapper
from pathlib import Path
from typing import Union, List

from fastapi import HTTPException, Response
from loguru import logger
from ossapi import User, Score, Mod

from app.config.settings import osu_api
from app.network.network import get_first_response
from app.osu_utils.file import cache_dir
from app.osu_utils.pp import get_ss_pp_info
from app.draw.beatmap import BeatmapImageStrategy, BeatmapSetImageStrategy


async def get_content_from_urls(url_list: list, max_attempts: int = 5) -> BytesIO:
    """
    尝试从URL列表中获取内容，最多重试max_attempts次。
    只有当响应的Content-Type为图片类型时才认为是成功的。
    """
    for attempt in range(max_attempts):
        try:
            response = await get_first_response(url_list)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'image/' in content_type:
                content = await response.aread()
                return BytesIO(content)
            else:
                logger.debug(f"Non-image content type received: {content_type}")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} of {max_attempts} failed: {e}")
            await asyncio.sleep(1)  # 简单的退避策略

    logger.error(f"Failed to download after {max_attempts} attempts")
    return BytesIO()  # 返回一个空的BytesIO对象表示失败


async def get_map_bg(set_id: int, map_id: int = None, bg_name: str = None) -> bytes:
    """
    获取 beatmap 背景图。
    """
    file_path = cache_dir / "beatmap" / "osu_file" / f"{set_id}"
    file_path.mkdir(parents=True, exist_ok=True)
    if bg_name:
        file_name = bg_name
    else:
        file_name = f"set.jpg"
    file_full_path = file_path / file_name

    if file_full_path.exists():
        return file_full_path.read_bytes()

    # 尝试下载背景图
    try:
        if bg_name and map_id:
            file_content = await download_map_bg(map_id, set_id, bg_name)
        else:
            file_content = await download_set_bg(set_id)
        if file_content.getbuffer().nbytes == 0:  # 确保内容非空
            raise ValueError("Downloaded file is empty")
    except Exception as e:
        logger.warning(f"Failed to get beatmap background, trying to get seasonal background: {e}")
        file_content = await download_seasonal_bg()

    with open(file_full_path, "wb") as f:
        f.write(file_content.getvalue())
    return file_content.getvalue()


async def download_map_bg(map_id: int, set_id: int = None, bg_name: str = None) -> BytesIO:
    """
    下载 beatmap 背景图。
    """
    url_list = [
        f"https://api.osu.direct/media/background/{map_id}",
        f"https://subapi.nerinyan.moe/bg/{map_id}",
    ]
    if set_id and bg_name:
        url_list.append(f'https://dl.sayobot.cn/beatmaps/files/{set_id}/{bg_name}')

    return await get_content_from_urls(url_list)


async def download_set_bg(set_id: int) -> BytesIO:
    """
    下载 beatmap set 背景图。
    """
    url_list = [f"https://assets.ppy.sh/beatmaps/{set_id}/covers/cover@2x.jpg"]
    return await get_content_from_urls(url_list)


async def download_seasonal_bg() -> BytesIO:
    """
    下载季节背景图。
    """
    seasonal_bg = osu_api.seasonal_backgrounds()
    url_list = [bg.url for bg in seasonal_bg.backgrounds]
    return await get_content_from_urls(url_list)


async def get_osu_file_path(beatmap_set_id: int, beatmap_id: int) -> Path:
    """
    获取 osu 文件路径
    :param beatmap_set_id:
    :param beatmap_id:
    :return:
    """
    path = cache_dir / "beatmap" / "osu_file" / f"{beatmap_set_id}"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    file_name = f"{beatmap_id}.osu"
    url = [f"https://osu.ppy.sh/osu/{beatmap_id}", f"https://api.osu.direct/osu/{beatmap_id}"]
    # 如果文件存在，直接读取文件
    if (path / file_name).exists():
        return path / file_name
    # 如果文件不存在，下载文件
    try:
        logger.info(f"Downloading osu file for {beatmap_id}")
        response = await get_first_response(url)
        with open(path / file_name, "wb") as f:
            f.write(response.content)

    except Exception as e:
        logger.error(f"Failed to get osu file: {e}")
        raise e

    return path / file_name


def get_bg_filename(file: Union[bytes, Path]) -> str:
    # 读取文件内容到text字符串
    if isinstance(file, bytes):
        text = TextIOWrapper(BytesIO(file), "utf-8").read()
    else:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

    # 使用正则表达式解析文本，找到所有匹配
    for match in re.finditer(r"\d,\d,\"(.+)\"", text):
        bg_candidate = match.group(1).strip()
        # 检查文件后缀是否为 jpg 或 png
        if bg_candidate.endswith('.jpg') or bg_candidate.endswith('.png') or bg_candidate.endswith('.jpeg'):
            return bg_candidate

    # 如果没有找到任何有效的匹配项，则返回默认文件名
    return "mapbg.png"


def calculate_circle_size(circle_size: float, mod) -> float:
    """
    计算 CS
    :param circle_size:
    :param mod:
    :return:
    """
    if Mod.HR in mod:
        circle_size = min(circle_size * 1.3, 10)
    elif Mod.EZ in mod:
        circle_size = min(circle_size * 0.5, 10)

    return circle_size


def calculate_hp(hp: float, mod) -> float:
    """
    计算 HP
    :param hp:
    :param mod:
    :return:
    """
    if Mod.HR in mod:
        hp = min(hp * 1.4, 10)
    elif Mod.EZ in mod:
        hp = min(hp * 0.5, 10)

    return hp


def calculate_bpm(bpm: float, mod) -> float:
    """
    计算 BPM
    :param bpm: 原 BPM
    :param mod: 游玩 Mod
    :return:
    """
    if Mod.DT in mod:
        bpm = bpm * 1.5
    elif Mod.HT in mod:
        bpm = bpm * 0.75

    return bpm


def calculate_length(length: int, mod) -> str:
    """
    计算长度
    :param length: 原长度, 秒
    :param mod:
    :return:
    """
    if Mod.DT in mod:
        length = int(length / 1.5)
    elif Mod.HT in mod:
        length = int(length / 0.75)

    length_str = f"{length // 60}:{length % 60:02d}"

    return length_str


async def get_info_img(beatmap_id: int, beatmapset_id: int, theme: str):
    """
    获取 beatmap 信息图片
    :param beatmapset_id:
    :param beatmap_id:
    :param theme:
    :return:
    """
    if not beatmap_id and not beatmapset_id:
        raise HTTPException(status_code=400, detail="Bad request")
    if beatmap_id:
        beatmap_info = osu_api.beatmap(beatmap_id=beatmap_id)
        if not beatmap_info:
            raise HTTPException(status_code=400, detail="Bad request")
        osu_file_path = await get_osu_file_path(beatmap_info.beatmapset().id, beatmap_info.id)
        ss_pp_info = get_ss_pp_info(osu_file_path, beatmap_info.mode_int, 0)
        mapper_info = osu_api.user(beatmap_info.beatmapset().user_id)
        bg_name = get_bg_filename(osu_file_path)
        map_bg = await get_map_bg(set_id=beatmap_info.beatmapset().id, map_id=beatmap_info.id, bg_name=bg_name)
        try:
            illustration = BeatmapImageStrategy(beatmap_info, ss_pp_info, mapper_info, bg_name, map_bg)
            image = await illustration.apply_theme(theme)
        except Exception as e:
            logger.error(f"An error occurred while generating beatmap image: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    else:
        beatmap_set_info = osu_api.beatmapset(beatmapset_id=beatmapset_id)
        try:
            illustration = BeatmapSetImageStrategy(beatmap_set_info)
            image = await illustration.apply_theme(theme)
        except Exception as e:
            logger.error(f"An error occurred while generating beatmap image: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")
