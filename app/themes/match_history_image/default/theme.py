import re
from datetime import datetime
from io import BytesIO
from statistics import mode
from typing import Union

from PIL import Image, ImageDraw
from loguru import logger
from ossapi import TeamType
from ossapi.models import MatchResponse, MatchEventType

from app.osu_utils.beatmap import get_map_bg
from app.config.settings import osu_api
from app.draw.fonts import *
from app.draw.utils import draw_fillet
from app.osu_utils.user import get_user_avatar
from app.themes.match_history_image.default.img_process import (preprocess_bg, get_score_diff, draw_stars_diff,
                                                                get_top3, get_top3_color)
from app.osu_utils.multiplayer import analyze_team_vs_game_history, get_win_side
from app.themes.theme_interface import ThemeStrategy
from app.themes.match_history_image.default.assets import HeaderImg, BodyImg, TeamBlue, TeamRed, get_mod_image


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[MatchResponse]) -> bytes:
        match_info = args[0]

        pattern = r"([^:]+): [\(\（](.+?)[\)\）] vs [\(\（](.+?)[\)\）]"
        match_name = re.search(pattern, match_info.match.name, re.IGNORECASE)
        game_history = []
        for sequence in match_info.events:
            if sequence.detail.type == MatchEventType.OTHER and sequence.game is not None:
                game_history.append(sequence.game)

        analyzed_game_history = analyze_team_vs_game_history(game_history)

        number_of_invalid_records = 0
        for game in game_history:
            if len(game.scores) == 0:
                number_of_invalid_records += 1

        # 判断比赛的队伍类型
        team_type_list = []
        invalid_user_list = []
        for game in game_history:
            team_type_list.append(game.team_type)
        team_type = mode(team_type_list)
        # TEAM_VS 模式下，分析比赛历史
        if team_type == TeamType.TEAM_VS:
            analyzed_result = analyze_team_vs_game_history(game_history)
            # 移除无效用户
            for game in game_history:
                for entry in game.scores:
                    if entry.score == 0:
                        invalid_user_list.append(entry.user_id)
                for entry in game.scores:
                    if entry.user_id in invalid_user_list:
                        game.scores.remove(entry)
            # 移除无效游戏
            for game in game_history:
                if len(game.scores) != analyzed_result["team_size"] * 2:
                    game_history.remove(game)

        # 绘制背景
        logger.info("开始绘制比赛历史地图信息")
        im = Image.new("RGBA", (1420, 280 + (280 * (len(game_history)) + 90)),
                       (31, 41, 46, 255))
        draw = ImageDraw.Draw(im)
        im.alpha_composite(Image.open(HeaderImg).convert("RGBA"), (0, 0))
        # 绘制标题
        if match_name:
            match_title = match_name.group(1)
            team_red = match_name.group(2)
            team_blue = match_name.group(3)
            draw.text((710, 120), "VS", font=Harmony_Sans_Bold_40, anchor="mm")
            draw.text((675, 120), f"{match_title}:  {team_red}", font=Harmony_Sans_Bold_40, anchor="rm")
            draw.text((745, 120), f"{team_blue}", font=Harmony_Sans_Bold_40, anchor="lm")
        # 绘制比分
        red_score = analyzed_game_history["red_score"]
        blue_score = analyzed_game_history["blue_score"]
        draw.text(
            (690, 180),
            f"{red_score}",
            font=Harmony_Sans_Bold_50,
            anchor="rm",
        )
        draw.text(
            (710, 180),
            f":",
            font=Harmony_Sans_Bold_50,
            anchor="mm",
        )
        draw.text(
            (730, 180),
            f"{blue_score}",
            font=Harmony_Sans_Bold_50,
            anchor="lm",
        )
        # 绘制时间
        draw.text(
            (1400, 260),
            f"{match_info.match.start_time.strftime('%Y-%m-%d %H:%M')} - {match_info.match.end_time.strftime('%H:%M')}",
            font=Harmony_Sans_Bold_25,
            anchor="rb",
        )
        # 在底部绘制当前时间
        draw.text(
            (1400, 280 * (len(game_history)) + 280 + 50),
            f"绘制时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=Harmony_Sans_Bold_20,
            anchor="rb",
        )

        # 绘制比赛信息
        number_of_invalid_records = 0
        total_stars = 0
        for i, game in enumerate(game_history):
            if len(game.scores) == 0:
                number_of_invalid_records += 1
                continue
            sequence = i - number_of_invalid_records
            logger.info(f"开始绘制第{sequence + 1}局")
            im.alpha_composite(Image.open(BodyImg).convert("RGBA"), (0, 280 * sequence + 280))
            # 计算分差
            score_diff = get_score_diff(game)
            draw.text(
                (710, 280 * sequence + 280 + 230),
                f"分差: {score_diff:,}",
                font=Harmony_Sans_Bold_25,
                anchor="mm",
            )
            # 绘制地图胜利方
            win_side = get_win_side(game)
            if win_side == "red":
                im.alpha_composite(Image.open(TeamRed).convert("RGBA"), (288, 280 * sequence + 280 + 36))
            elif win_side == "blue":
                im.alpha_composite(Image.open(TeamBlue).convert("RGBA"), (838, 280 * sequence + 280 + 36))
            gutter = 570 // (analyzed_game_history["team_size"] + 1)
            # 获取top3分数
            top3 = get_top3(game.scores)
            # 绘制玩家分数以及头像
            # 红队
            slot = 0
            score_img = Image.new("RGBA", (550, 215), (205, 205, 205, 0))
            score_draw = ImageDraw.Draw(score_img)
            for entry in game.scores:
                if entry.match.team == "blue":
                    continue
                user_id = entry.user_id
                user_info = next(
                    (user for user in match_info.users if user.id == user_id), (None, None, None)
                )
                if user_info is None:
                    continue
                # 如果是top3则在头像上圆形颜色背景以及名次
                if (user_id, entry.score) in top3:
                    color = get_top3_color(top3.index((user_id, entry.score)) + 1)
                    left = (slot + 1) * gutter - 15
                    top = 10
                    right = left + 30
                    bottom = top + 30
                    score_draw.ellipse(
                        [left, top, right, bottom],
                        fill=color
                    )
                    score_draw.text(
                        ((slot + 1) * gutter, 25),
                        f"{top3.index((user_id, entry.score)) + 1}",
                        font=Harmony_Sans_Bold_20,
                        anchor="mm",
                        fill="black"
                    )
                # 绘制头像
                user_icon = await get_user_avatar(user_info.id, user_info.avatar_url)
                user_icon = Image.open(BytesIO(user_icon)).convert("RGBA").resize((60, 60))
                user_icon = draw_fillet(user_icon, 10)
                score_img.alpha_composite(user_icon, ((slot + 1) * gutter - 30, 45))
                # 绘制用户名
                score_draw.text(
                    ((slot + 1) * gutter, 120),
                    f"{user_info.username}",
                    font=Harmony_Sans_Reg_20,
                    anchor="mm",
                )
                # 绘制分数
                score_draw.text(
                    ((slot + 1) * gutter, 145),
                    f"{entry.score:,}",
                    font=Harmony_Sans_Reg_20,
                    anchor="mm",
                )
                # 绘制ACC
                score_draw.text(
                    ((slot + 1) * gutter, 170),
                    f"{entry.accuracy * 100:.2f}%",
                    font=Harmony_Sans_Reg_20,
                    anchor="mm",
                )
                slot += 1
            im.alpha_composite(score_img, (10, 280 * sequence + 280 + 35))
            score_img.close()

            # 蓝队
            slot = 0
            score_img = Image.new("RGBA", (550, 215), (205, 205, 205, 0))
            score_draw = ImageDraw.Draw(score_img)
            for entry in game.scores:
                if entry.match.team == "red":
                    continue
                user_id = entry.user_id
                user_info = next(
                    (user for user in match_info.users if user.id == user_id), (None, None, None)
                )
                if user_info is None:
                    continue
                # 如果是top3则在头像上绘制圆形颜色背景以及名次
                if (user_id, entry.score) in top3:
                    color = get_top3_color(top3.index((user_id, entry.score)) + 1)
                    left = (slot + 1) * gutter - 15
                    top = 10
                    right = left + 30
                    bottom = top + 30
                    score_draw.ellipse(
                        [left, top, right, bottom],
                        fill=color
                    )
                    score_draw.text(
                        ((slot + 1) * gutter, 25),
                        f"{top3.index((user_id, entry.score)) + 1}",
                        font=Harmony_Sans_Bold_20,
                        anchor="mm",
                        fill="black"
                    )
                # 绘制头像
                user_icon = await get_user_avatar(user_info.id, user_info.avatar_url)
                user_icon = Image.open(BytesIO(user_icon)).convert("RGBA").resize((60, 60))
                user_icon = draw_fillet(user_icon, 10)
                score_img.alpha_composite(user_icon, ((slot + 1) * gutter - 30, 45))
                # 绘制用户名
                score_draw.text(
                    ((slot + 1) * gutter, 120),
                    f"{user_info.username}",
                    font=Harmony_Sans_Reg_20,
                    anchor="mm",
                )
                # 绘制分数
                score_draw.text(
                    ((slot + 1) * gutter, 145),
                    f"{entry.score:,}",
                    font=Harmony_Sans_Reg_20,
                    anchor="mm",
                )
                # 绘制ACC
                score_draw.text(
                    ((slot + 1) * gutter, 170),
                    f"{entry.accuracy * 100:.2f}%",
                    font=Harmony_Sans_Reg_20,
                    anchor="mm",
                )
                slot += 1
            im.alpha_composite(score_img, (830, 280 * sequence + 280 + 35))

            # 获取地图
            map_info = game.beatmap
            # 绘制bg
            if not map_info:
                logger.error(f"第{sequence + 1}局地图信息为空")
                continue
            map_bg = await get_map_bg(set_id=map_info.beatmapset_id)
            bg = Image.open(BytesIO(map_bg)).convert("RGBA")
            preprocessed_bg = preprocess_bg(bg)
            im.alpha_composite(preprocessed_bg, (590, 280 * sequence + 280 + 40))
            # 绘制地图信息
            map_title = f"{game.beatmap.beatmapset().title}"
            text_width = draw.textlength(map_title, font=Harmony_Sans_Bold_30)
            if text_width > 200:
                for t in range(1, len(map_title)):
                    if draw.textlength(map_title[:t], font=Harmony_Sans_Bold_30) > 200:
                        map_title = map_title[:t - 1] + "..."
                        break
            draw.text(
                (600, 280 * sequence + 325),
                f"{map_title}",
                font=Harmony_Sans_Bold_30,
                anchor="lt",
            )
            artist = f"{game.beatmap.beatmapset().artist}"
            text_width = draw.textlength(artist, font=Harmony_Sans_Reg_20)
            if text_width > 180:
                for t in range(1, len(artist)):
                    if draw.textlength(artist[:t], font=Harmony_Sans_Reg_20) > 180:
                        artist = artist[:t - 1] + "..."
                        break
            draw.text(
                (600, 280 * sequence + 357),
                f"{artist}",
                font=Harmony_Sans_Reg_20,
                anchor="lt",
            )
            diff = f"{game.beatmap.version}"
            text_width = draw.textlength(diff, font=Harmony_Sans_Reg_20)
            if text_width > 180:
                for t in range(1, len(diff)):
                    if draw.textlength(diff[:t], font=Harmony_Sans_Reg_20) > 180:
                        diff = diff[:t - 1] + "..."
                        break
            draw.text(
                (600, 280 * sequence + 380),
                f"{diff}",
                font=Harmony_Sans_Reg_20,
                anchor="lt",
            )
            beatmap_id = f"{game.beatmap.id}"
            draw.text(
                (820, 280 * sequence + 415),
                f"b{beatmap_id}",
                font=Harmony_Sans_Bold_20,
                anchor="rt",
            )

            # 绘制mods
            for mods_num, s_mods in enumerate(game.mods):
                if s_mods == "NF":
                    continue
                mods_bg = get_mod_image(str(s_mods))
                mods_img = Image.open(mods_bg).convert("RGBA")
                im.alpha_composite(mods_img, (550 + 50 * mods_num, 280 * i + 280 + 170))
            # 难度星数
            attribute_data = osu_api.beatmap_attributes(beatmap_id=game.beatmap_id, mods=game.mods, ruleset=game.mode)
            stars = attribute_data.attributes.star_rating
            total_stars += stars
            stars_img = draw_stars_diff(stars)
            stars_img = stars_img.resize((90, 36))
            im.alpha_composite(stars_img, (740, 280 * sequence + 280 + 167))
            draw.text(
                (787, 280 * sequence + 280 + 175),
                f"{stars:.2f}★",
                font=Harmony_Sans_Reg_25,
                anchor="mt",
            )

        avg_stars = total_stars / (len(game_history) - number_of_invalid_records)
        draw.text(
            (1400, 220),
            f"AVG SR: {avg_stars:.2f}",
            font=Harmony_Sans_Bold_30,
            anchor="rm",
        )

        byt = BytesIO()
        im.save(byt, format="PNG")
        im.close()

        return byt.getvalue()


def get_theme_strategy():
    return DefaultTheme()
