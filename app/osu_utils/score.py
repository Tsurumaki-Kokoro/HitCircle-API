from fastapi import HTTPException, Response
from loguru import logger
from tortoise.exceptions import DoesNotExist

from app.config.settings import osu_api
from app.draw.score import ScoreImageStrategy
from app.osu_utils.beatmap import get_osu_file_path, get_map_bg, get_bg_filename
from app.osu_utils.pp import PPCalculator
from app.osu_utils.user import game_mode_int_to_string
from app.user.models import UserModel


async def generate_play_record_img(platform: str, platform_uid: int,
                                   record_type: str, game_mode: int = None,
                                   include_fails: bool = False, theme: str = "default",
                                   best_index: int = None):
    # 获取用户信息
    try:
        user = await UserModel.get(platform_uid=platform_uid, platform=platform)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    user_info = osu_api.user(user.osu_uid)

    # 获取游玩记录
    if not game_mode:
        game_mode = game_mode_int_to_string(user.game_mode)
    else:
        game_mode = game_mode_int_to_string(game_mode)

    params = {
        "user_id": user_info.id,
        "mode": game_mode,
        "type": record_type
    }

    # 获取游玩记录, 可扩展
    if record_type == "recent":
        params["include_fails"] = include_fails
    elif record_type == "best":
        params["limit"] = 1
        params["offset"] = best_index - 1

    try:
        logger.info(f"Getting play record for user {user_info.username}")
        play_records = osu_api.user_scores(**params)
    except ValueError as e:
        logger.error(f"Error when getting play record: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if len(play_records) == 0:
        raise HTTPException(status_code=404, detail=f"No {record_type} play record found")

    # 获取 beatmap attributes
    beatmap_attributes = osu_api.beatmap_attributes(
        beatmap_id=play_records[0].beatmap.id,
        mods=play_records[0].mods.value,
        ruleset=game_mode
    )
    # 获取谱面文件路径, 计算pp
    osu_file_path = await get_osu_file_path(play_records[0].beatmapset.id, play_records[0].beatmap.id)
    pp_calculate = PPCalculator(play_records[0], osu_file_path)
    bg_name = get_bg_filename(osu_file_path)
    map_bg = await get_map_bg(map_id=play_records[0].beatmap.id, set_id=play_records[0].beatmapset.id, bg_name=bg_name)
    # 绘制图片
    try:
        illustration = ScoreImageStrategy(play_records[0], user_info, pp_calculate, map_bg, beatmap_attributes)
        image = await illustration.apply_theme(theme)
    except Exception as e:
        logger.error(f"Error when drawing image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")


async def generate_user_score_img(platform: str, platform_uid: int, beatmap_id: int,
                                  mods: str = None, theme: str = "default"):
    # 获取用户信息
    try:
        user = await UserModel.get(platform_uid=platform_uid, platform=platform)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    user_info = osu_api.user(user.osu_uid)

    try:
        logger.info(f"Getting beatmap attributes for beatmap {beatmap_id}")
        play_record = osu_api.beatmap_user_score(
            beatmap_id=beatmap_id,
            user_id=user_info.id,
            mods=mods
        ).score
    except ValueError as e:
        logger.error(f"Error when getting user score: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # 获取 beatmap attributes
    beatmap_attributes = osu_api.beatmap_attributes(
        beatmap_id=play_record.beatmap.id,
        mods=play_record.mods.value,
        ruleset=play_record.mode
    )
    # 获取谱面文件路径, 计算pp
    osu_file_path = await get_osu_file_path(play_record.beatmap.beatmapset_id, play_record.beatmap.id)
    pp_calculate = PPCalculator(play_record, osu_file_path)
    bg_name = get_bg_filename(osu_file_path)
    map_bg = await get_map_bg(map_id=play_record.beatmap.id, set_id=play_record.beatmap.beatmapset_id, bg_name=bg_name)
    # 绘制图片
    try:
        illustration = ScoreImageStrategy(play_record, user_info, pp_calculate, map_bg, beatmap_attributes)
        image = await illustration.apply_theme(theme)
    except Exception as e:
        logger.error(f"Error when drawing image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")
