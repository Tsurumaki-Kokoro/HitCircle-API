import re
from datetime import datetime
from io import BytesIO
from statistics import mode
from typing import Union

from PIL import Image, ImageDraw
from loguru import logger
from ossapi.models import MatchResponse, MatchEventType, TeamType

from app.osu_utils.multiplayer import PlayerMatchStats, analyze_team_vs_game_history, analyze_head_to_head_history
from app.osu_utils.rating import PlayerRatingCalculation
from app.draw.fonts import *
from app.draw.utils import draw_rounded_rectangle, crop_image, draw_fillet
from app.osu_utils.user import get_user_avatar

from app.themes.theme_interface import ThemeStrategy
from app.themes.rating_image.default.assets import HeaderImg, TeamRed, TeamBlue
from app.themes.rating_image.default.img_process import rating_to_wn8_hex, score_to_3digit


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[MatchResponse, str]) -> bytes:
        match_info = args[0]
        algorithm = args[1]

        pattern = r"([^:]+): [\(\（](.+?)[\)\）] vs [\(\（](.+?)[\)\）]"
        match_name = re.search(pattern, match_info.match.name, re.IGNORECASE)
        game_history = []
        for sequence in match_info.events:
            if sequence.detail.type == MatchEventType.OTHER and sequence.game is not None:
                game_history.append(sequence.game)
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
        im = Image.new("RGBA", (1020, 280 + 170 * (len(match_info.users) - len(invalid_user_list)) + 90),
                       (31, 41, 46, 255))

        draw = ImageDraw.Draw(im)
        im.alpha_composite(Image.open(HeaderImg).convert("RGBA"), (0, 0))

        if team_type == TeamType.TEAM_VS:
            match_title = match_name.group(1)
            team_red = match_name.group(2)
            team_blue = match_name.group(3)
            text = f"{match_title}:  {team_red} VS {team_blue}"
            draw.text((510, 130), text, font=Harmony_Sans_Bold_40, anchor="mm")
        elif team_type == TeamType.HEAD_TO_HEAD:
            match_title = match_info.match.name
            draw.text((510, 130), f"{match_title}", font=Harmony_Sans_Bold_40, anchor="mm")

        # 绘制时间
        draw.text(
            (950, 220),
            f"{match_info.match.start_time.strftime('%Y-%m-%d %H:%M')} - {match_info.match.end_time.strftime('%H:%M')}",
            font=Harmony_Sans_Bold_25,
            anchor="rb",
        )
        # 在底部绘制当前时间
        draw.text(
            (950, 170 * (len(match_info.users) - len(invalid_user_list)) + 280 + 50),
            f"绘制时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=Harmony_Sans_Bold_20,
            anchor="rb",
        )

        player_statistic_list = []
        for i, user in enumerate(match_info.users):
            calculater = PlayerRatingCalculation(match_info)
            rating = calculater.get_rating(user.id, algorithm)
            player_stats = PlayerMatchStats(user, game_history)
            player_statistic_list.append((user, player_stats, rating))

        player_statistic_list.sort(key=lambda x: x[2], reverse=True)

        for i, (user, player_stats, rating) in enumerate(player_statistic_list):
            # HEAD_TO_HEAD 模式下，分析比赛历史
            if team_type == TeamType.HEAD_TO_HEAD:
                head_to_head_result = analyze_head_to_head_history(game_history, user.id)
            if player_stats.total_score == 0:
                continue
            if player_stats.player_team == "red":
                fill = '#d32f2e'
                background = Image.open(TeamRed).convert("RGBA")
            else:
                fill = '#00a0e8'
                background = Image.open(TeamBlue).convert("RGBA")
            rating_color = rating_to_wn8_hex(rating, player_stats.win_rate)
            draw_rounded_rectangle(draw, ((140, 170 * i + 280), (336, 170 * i + 390)), 20, fill=fill)
            draw_rounded_rectangle(draw, ((736, 170 * i + 280), (966, 170 * i + 389)), 20, fill=rating_color[1])
            background = crop_image(background, 650, 110)
            background = draw_fillet(background, 20)
            im.paste(background, (160, 170 * i + 280), background)

            avatar = await get_user_avatar(user.id, user.avatar_url)
            avatar = Image.open(BytesIO(avatar)).convert("RGBA")
            avatar = crop_image(avatar, 176, 110)
            avatar = draw_fillet(avatar, 20)
            im.paste(avatar, (160, 170 * i + 280), avatar)

            draw.text(
                (40, 170 * i + 335),
                f"#{i + 1}",
                font=Harmony_Sans_Bold_40,
                fill="#ffffff",
                anchor="lm",
            )

            draw.text(
                (350, 170 * i + 306),
                f"{user.username}",
                font=Harmony_Sans_Bold_30,
                fill="#ffffff",
                anchor="lm",
            )

            draw.text(
                (350, 170 * i + 341),
                f"Total Score: {score_to_3digit(player_stats.total_score)}"
                f" ({score_to_3digit(player_stats.average_score)})",
                font=Harmony_Sans_Bold_20,
                fill="#bbbbbb",
                anchor="lm",
            )

            if team_type == TeamType.TEAM_VS:
                draw.text(
                    (350, 170 * i + 366),
                    f"Win Rate: {player_stats.win_rate:.2%} ({player_stats.win_and_lose[0]}W"
                    f"-{player_stats.win_and_lose[1]}L)",
                    font=Harmony_Sans_Bold_20,
                    fill="#bbbbbb",
                    anchor="lm",
                )
            elif team_type == TeamType.HEAD_TO_HEAD:
                top1_rate = head_to_head_result["top1_rate"]
                top1_count = head_to_head_result["number_of_games_top1"]
                game_amount = head_to_head_result["number_of_games"]
                draw.text(
                    (350, 170 * i + 366),
                    f"Top 1 Rate: {top1_rate:.2%} ({top1_count} W/{game_amount} P)",
                    font=Harmony_Sans_Bold_20,
                    fill="#bbbbbb",
                    anchor="lm",
                )

            draw.text(
                (840, 170 * i + 340),
                f"{rating:.2f}",
                font=Harmony_Sans_Bold_45,
                fill="#ffffff",
                anchor="lm",
            )

        byt = BytesIO()
        im.save(byt, format="PNG")
        im.close()

        return byt.getvalue()


def get_theme_strategy():
    return DefaultTheme()
