from datetime import datetime, timedelta

from fastapi import HTTPException, Response, UploadFile
from loguru import logger
from tortoise.exceptions import DoesNotExist

from app.config.settings import osu_api
from app.draw.user_info import UserInfoImageStrategy, UserBPAnalyzeImageStrategy
from app.osu_utils.user import game_mode_int_to_string
from app.osu_utils.file import cache_dir
from app.osu_utils.pp import find_optimal_new_pp
from app.user.models import UserModel, UserOsuInfoHistory


async def generate_player_info_img(platform: str, platform_uid: str, game_mode: int = None, compare_with: int = None,
                                   theme: str = "default"):
    # 获取用户信息
    try:
        user = await UserModel.get(platform_uid=platform_uid, platform=platform)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    # 获取游玩记录
    if not game_mode:
        game_mode = game_mode_int_to_string(user.game_mode)
    else:
        game_mode = game_mode_int_to_string(game_mode)

    # 获取osu玩家信息
    logger.info(f"Getting player info for user {user.osu_uid}")
    osu_player_info = osu_api.user(user=user.osu_uid, mode=game_mode, key="id")
    osu_player_scores = osu_api.user_scores(user_id=user.osu_uid, type="best", mode=game_mode, limit=100)

    # 获取对比玩家信息
    now = datetime.now()
    if compare_with:
        compare_date = now - timedelta(days=compare_with)
        try:
            osu_player_history_info = await UserOsuInfoHistory.get(
                osu_uid=user.osu_uid, game_mode=game_mode, date=compare_date
            )
        except DoesNotExist:
            try:
                osu_player_history_info = await (UserOsuInfoHistory.filter(osu_uid=user.osu_uid, game_mode=game_mode)
                                                 .order_by("date").first())
            except DoesNotExist:
                osu_player_history_info = None
    else:
        osu_player_history_info = None

    # 绘制图片
    try:
        illustration = UserInfoImageStrategy(osu_player_info, osu_player_history_info, game_mode.upper(),
                                             osu_player_scores)
        image = await illustration.apply_theme(theme)
    except Exception as e:
        logger.error(f"An error occurred while generating user info image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")


async def save_user_info(uid: str, game_mode: int):
    mode = game_mode_int_to_string(game_mode)
    osu_player_info = osu_api.user(uid, mode=mode, key="id")
    try:
        user_database_instance = await UserOsuInfoHistory.get(
            osu_uid=uid,
            game_mode=game_mode,
            date=datetime.now().date(),
        )
        user_database_instance.country_rank = osu_player_info.statistics.country_rank
        user_database_instance.global_rank = osu_player_info.statistics.global_rank
        user_database_instance.pp = osu_player_info.statistics.pp
        user_database_instance.accuracy = osu_player_info.statistics.hit_accuracy
        user_database_instance.play_count = osu_player_info.statistics.play_count
        user_database_instance.play_time = osu_player_info.statistics.play_time
        user_database_instance.total_hits = osu_player_info.statistics.total_hits

        await user_database_instance.save()
    except DoesNotExist:
        await UserOsuInfoHistory.create(
            osu_uid=uid,
            game_mode=game_mode,
            country_rank=osu_player_info.statistics.country_rank,
            global_rank=osu_player_info.statistics.global_rank,
            pp=osu_player_info.statistics.pp,
            accuracy=osu_player_info.statistics.hit_accuracy,
            play_count=osu_player_info.statistics.play_count,
            play_time=osu_player_info.statistics.play_time,
            total_hits=osu_player_info.statistics.total_hits,
            date=datetime.now().date()
        )


async def update_user_info_background(platform: str, platform_uid: str, file: UploadFile) -> dict:
    try:
        user = await UserModel.get(platform=platform, platform_uid=platform_uid)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    # 保存背景图片
    path = cache_dir / "user" / f"{user.osu_uid}"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    file_name = "info.png"
    with open((path / file_name), "wb") as f:
        f.write(await file.read())

    return {"message": "Background updated successfully"}


async def generate_player_pp_control_result(platform: str, platform_uid: str, pp: float):
    # 获取用户信息
    try:
        user = await UserModel.get(platform_uid=platform_uid, platform=platform)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    user_info = osu_api.user(user.osu_uid)

    params = {
        "user_id": user_info.id,
        "mode": game_mode_int_to_string(user.game_mode),
        "type": "best",
        "limit": 100,
        "offset": 0,
    }

    try:
        logger.info(f"Getting best 100 play record for user {user_info.username}")
        play_records = osu_api.user_scores(**params)
    except ValueError as e:
        logger.error(f"Error when getting play record: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if len(play_records) == 0:
        raise HTTPException(status_code=404, detail="No play record found")

    pp_list = []
    for record in play_records:
        pp_list.append(record.pp)
    required_pp = find_optimal_new_pp(pp_list, pp)

    return {"required_pp": required_pp}


async def generate_player_pp_analyze_img(platform: str, platform_uid: str, theme: str):
    # 获取用户信息
    try:
        user = await UserModel.get(platform_uid=platform_uid, platform=platform)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    user_info = osu_api.user(user.osu_uid)

    params = {
        "user_id": user_info.id,
        "mode": game_mode_int_to_string(user.game_mode),
        "type": "best",
        "limit": 100,
        "offset": 0,
    }

    try:
        logger.info(f"Getting best 100 play record for user {user_info.username}")
        play_records = osu_api.user_scores(**params)
    except ValueError as e:
        logger.error(f"Error when getting play record: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if len(play_records) == 0:
        raise HTTPException(status_code=404, detail="No play record found")

    try:
        illustration = UserBPAnalyzeImageStrategy(user_info, play_records)
        image = await illustration.apply_theme(theme)
    except Exception as e:
        logger.error(f"An error occurred while generating user info image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")
