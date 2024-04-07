from datetime import timedelta, datetime
from io import BytesIO
from typing import Union, Optional, List

from PIL import Image, ImageDraw, ImageSequence
from ossapi.models import Score, User

from app.draw.flags import get_region_flag
from app.draw.fonts import Harmony_Sans_Bold_40, Harmony_Sans_Bold_50, Harmony_Sans_Bold_30, Harmony_Sans_Bold_25, \
    Harmony_Sans_Bold_20, Harmony_Sans_Bold_35
from app.draw.utils import draw_fillet
from app.osu_utils.user import get_user_badge, get_user_avatar, get_info_bg
from app.themes.theme_interface import ThemeStrategy
from app.themes.user_info_image.default.assets import get_layout_image, SupporterBadge, get_exp_bar_image
from app.user.models import UserOsuInfoHistory


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[User, UserOsuInfoHistory | None, str, List[Score]]) -> bytes:
        # 初始化参数
        user_info = args[0]
        history_info = args[1]
        game_mode = args[2]
        user_scores = args[3]

        if not history_info:
            history_country_rank = user_info.statistics.country_rank
            history_global_rank = user_info.statistics.global_rank
            history_pp = user_info.statistics.pp
            history_accuracy = user_info.statistics.hit_accuracy
            history_play_count = user_info.statistics.play_count
            history_total_hits = user_info.statistics.total_hits
            history_date = datetime.today().date()

        else:
            history_country_rank = history_info.country_rank
            history_global_rank = history_info.global_rank
            history_pp = history_info.pp
            history_accuracy = history_info.accuracy
            history_play_count = history_info.play_count
            history_total_hits = history_info.total_hits
            history_date = history_info.date

        # 初始化图片
        im = Image.new("RGBA", (1000, 1350))
        draw = ImageDraw.Draw(im)
        # 获取背景
        user_bg = await get_info_bg(user_info.id)
        if user_bg:
            user_bg = Image.open(BytesIO(user_bg))
            bg = user_bg.convert("RGBA")
            width, height = bg.size
            bg_ratio = height / width
            ratio = 1350 / 1000
            if bg_ratio > ratio:
                height = ratio * width
            else:
                width = height / ratio
            x, y = bg.size
            x, y = (x - width) // 2, (y - height) // 2
            bg = bg.crop((x, y, x + width, y + height)).resize((1000, 1350))
            im.alpha_composite(bg, (0, 0))
        # 底图
        layout = Image.open(get_layout_image())
        im.alpha_composite(layout)
        # badges
        if len(user_info.badges) > 0:
            for i, badge in enumerate(user_info.badges):
                badge_img = await get_user_badge(user_info.id, badge.image_2x_url, badge.description)
                badge_img = Image.open(badge_img).convert("RGBA").resize((86, 40))
                if len(user_info.badges) <= 9:
                    length = 50 + 100 * i
                    height = 510
                elif i < 9:
                    length = 50 + 100 * i
                    height = 486
                else:
                    length = 50 + 100 * (i - 9)
                    height = 534
                im.alpha_composite(badge_img, (length, height))
        # flags
        region_flag = get_region_flag(user_info.country_code)
        region_img = Image.open(region_flag).convert("RGBA").resize((80, 54))
        im.alpha_composite(region_img, (400, 394))
        # supporter
        if user_info.is_supporter:
            supporter_img = Image.open(SupporterBadge).convert("RGBA").resize((60, 60))
            im.alpha_composite(supporter_img, (50, 394))
        # Exp bar
        if user_info.statistics.level.progress != 0:
            left, center, right = get_exp_bar_image()
            left = Image.open(left).convert("RGBA")
            center = Image.open(center).convert("RGBA")
            right = Image.open(right).convert("RGBA")
            exp_width = user_info.statistics.level.progress * 7 - 3
            im.alpha_composite(left, (50, 646))
            im.alpha_composite(center.resize((exp_width, 10)), (54, 646))
            im.alpha_composite(right, (int(54 + exp_width), 646))
        # 模式
        draw.text((930, 50), f"{game_mode}", font=Harmony_Sans_Bold_40, anchor="rm")
        # 用户名
        draw.text((400, 205), user_info.username, font=Harmony_Sans_Bold_50, anchor="lm")
        # 地区排名
        op, value = info_calc(user_info.statistics.country_rank, history_country_rank, rank=True)
        if not user_info.statistics.country_rank:
            t_crank = "#0"
        else:
            t_crank = (
                f"#{user_info.statistics.country_rank:,}({op}{value:,})"
                if value != 0
                else f"#{user_info.statistics.country_rank:,}"
            )
        draw.text((495, 448), t_crank, font=Harmony_Sans_Bold_30, anchor="lb")
        # 等级
        draw.text(
            (900, 650), str(user_info.statistics.level.current), font=Harmony_Sans_Bold_25, anchor="mm"
        )
        # 经验百分比
        draw.text(
            (750, 660), f"{user_info.statistics.level.progress}%", font=Harmony_Sans_Bold_20, anchor="rt"
        )
        # 全球排名
        if not user_info.statistics.global_rank:
            draw.text((55, 785), "#0", font=Harmony_Sans_Bold_35, anchor="lt")
        else:
            draw.text(
                (55, 785),
                f"#{user_info.statistics.global_rank:,}",
                font=Harmony_Sans_Bold_35,
                anchor="lt",
            )
        op, value = info_calc(user_info.statistics.global_rank, history_global_rank, rank=True)
        if value != 0:
            draw.text((65, 820), f"{op}{value:,}", font=Harmony_Sans_Bold_20, anchor="lt")
        # pp
        draw.text((295, 785), f"{user_info.statistics.pp:,}", font=Harmony_Sans_Bold_35, anchor="lt")
        op, value = info_calc(user_info.statistics.pp, history_pp, pp=True)
        if value != 0:
            draw.text((305, 820), f"{op}{int(value)}", font=Harmony_Sans_Bold_20)
        # SS - A 数量
        draw.text((493, 788), f"{user_info.statistics.grade_counts.ssh}", font=Harmony_Sans_Bold_30, anchor="mt")
        draw.text((593, 788), f"{user_info.statistics.grade_counts.ss}", font=Harmony_Sans_Bold_30, anchor="mt")
        draw.text((693, 788), f"{user_info.statistics.grade_counts.sh}", font=Harmony_Sans_Bold_30, anchor="mt")
        draw.text((793, 788), f"{user_info.statistics.grade_counts.s}", font=Harmony_Sans_Bold_30, anchor="mt")
        draw.text((893, 788), f"{user_info.statistics.grade_counts.a}", font=Harmony_Sans_Bold_30, anchor="mt")
        # Ranked Score
        draw.text(
            (935, 895), f"{user_info.statistics.ranked_score:,}", font=Harmony_Sans_Bold_40, anchor="rt"
        )
        # Accuracy
        op, value = info_calc(user_info.statistics.hit_accuracy, history_accuracy)
        t_acc = (
            f"{user_info.statistics.hit_accuracy:.2f}%({op}{value:.2f}%)"
            if value != 0
            else f"{user_info.statistics.hit_accuracy:.2f}%"
        )
        draw.text((935, 965), t_acc, font=Harmony_Sans_Bold_40, anchor="rt")
        # 游玩次数
        op, value = info_calc(user_info.statistics.play_count, history_play_count)
        t_pc = (
            f"{user_info.statistics.play_count:,}({op}{value:,})"
            if value != 0
            else f"{user_info.statistics.play_count:,}"
        )
        draw.text((935, 1035), t_pc, font=Harmony_Sans_Bold_40, anchor="rt")
        # 总分
        draw.text(
            (935, 1105), f"{user_info.statistics.total_score:,}", font=Harmony_Sans_Bold_40, anchor="rt"
        )
        # 总命中
        op, value = info_calc(user_info.statistics.total_hits, history_total_hits)
        t_count = (
            f"{user_info.statistics.total_hits:,}({op}{value:,})"
            if value != 0
            else f"{user_info.statistics.total_hits:,}"
        )
        draw.text((935, 1175), t_count, font=Harmony_Sans_Bold_40, anchor="rt")
        # 游玩时间
        sec = timedelta(seconds=user_info.statistics.play_time)
        d_time = datetime(1, 1, 1) + sec
        t_time = "%dd %dh %dm %ds" % (sec.days, d_time.hour, d_time.minute, d_time.second)
        draw.text((935, 1245), t_time, font=Harmony_Sans_Bold_40, anchor="rt")
        # 底部时间对比
        if history_date != datetime.today().date():
            day_delta = datetime.today() - history_date
            time = day_delta.days
            current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            draw.text((260, 1305), current_time, font=Harmony_Sans_Bold_25, anchor="la")
            text = f"| 数据对比于 {time} 天前"
            draw.text((515, 1305), text, font=Harmony_Sans_Bold_25, anchor="la")
        else:
            current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            draw.text((380, 1305), current_time, font=Harmony_Sans_Bold_25, anchor="la")
        # 头像
        gif_frames = []
        user_icon = await get_user_avatar(user_info.id, user_info.avatar_url)
        if not getattr(user_icon, "is_animated", False):
            icon_bg = Image.open(BytesIO(user_icon)).convert("RGBA").resize((300, 300))
            icon_img = draw_fillet(icon_bg, 25)
            im.alpha_composite(icon_img, (50, 148))
            byt = BytesIO()
            im.save(byt, "png")
            im.close()
            icon_bg.close()
            return byt.getvalue()
        for gif_frame in ImageSequence.Iterator(user_icon):
            # 将 GIF 图片中的每一帧转换为 RGBA 模式
            gif_frame = gif_frame.convert("RGBA").resize((300, 300))
            gif_frame = draw_fillet(gif_frame, 25)
            # 创建一个新的 RGBA 图片，将 PNG 图片作为背景，将当前帧添加到背景上
            rgba_frame = Image.new("RGBA", im.size, (0, 0, 0, 0))
            rgba_frame.paste(im, (0, 0), im)
            rgba_frame.paste(gif_frame, (50, 148), gif_frame)
            # 将 RGBA 图片转换为 RGB 模式，并添加到 GIF 图片中
            gif_frames.append(rgba_frame)
        gif_bytes = BytesIO()
        # 保存 GIF 图片
        gif_frames[0].save(
            gif_bytes, format="gif", save_all=True, append_images=gif_frames[1:]
        )
        # 输出
        gif_frames[0].close()
        return gif_bytes.getvalue()


def info_calc(
        n1: Optional[float], n2: Optional[float], rank: bool = False, pp: bool = False
):
    if not n1 or not n2:
        return "", 0
    num = n1 - n2
    if num < 0:
        if rank:
            op, value = "↑", num * -1
        elif pp:
            op, value = "↓", num * -1
        else:
            op, value = "-", num * -1
    elif num > 0:
        if rank:
            op, value = "↓", num
        elif pp:
            op, value = "↑", num
        else:
            op, value = "+", num
    else:
        op, value = "", 0
    return [op, value]


def get_theme_strategy():
    return DefaultTheme()
