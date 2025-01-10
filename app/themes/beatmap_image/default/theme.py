from datetime import timedelta
from io import BytesIO
from typing import Union

from PIL import Image, ImageDraw
from ossapi.models import Beatmap, User
from rosu_pp_py import PerformanceAttributes

from app.draw.fonts import *
from app.draw.utils import draw_fillet
from app.osu_utils.user import get_user_avatar
from app.themes.beatmap_image.default.assets import MapBg, ManiaMapBg, IconLs
from app.themes.beatmap_image.default.img_process import preprocess_bg, draw_stars_diff
from app.themes.theme_interface import ThemeStrategy


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[Beatmap, PerformanceAttributes, User, str, bytes]) -> bytes:
        # 初始化参数
        beatmap_info = args[0]
        ss_pp_info = args[1]
        mapper_info = args[2]
        bg_name = args[3]
        map_bg = Image.open(BytesIO(args[4])).convert("RGBA")
        # 初始化画布
        im = Image.new("RGBA", (1200, 600))
        draw = ImageDraw.Draw(im)
        # 绘制背景
        processed_bg = await preprocess_bg(map_bg)
        im.alpha_composite(processed_bg, (0, 0))
        # 绘制layout
        if beatmap_info.rule_set in {3, 7}:
            layout = Image.open(ManiaMapBg).convert("RGBA")
        else:
            layout = Image.open(MapBg).convert("RGBA")
        im.alpha_composite(layout, (0, 0))
        # 绘制模式
        draw.text((50, 65), IconLs[beatmap_info.mode.name.lower()], font=EXTRA_30, anchor="lt")
        # 绘制星级
        stars_bg = draw_stars_diff(ss_pp_info.difficulty.stars)
        stars_img = stars_bg.resize((80, 30))
        im.alpha_composite(stars_img, (90, 65))
        if ss_pp_info.difficulty.stars < 6.5:
            color = (0, 0, 0, 255)
        else:
            color = (255, 217, 102, 255)
        # 星级
        draw.text((100, 80), f"★{ss_pp_info.difficulty.stars:.2f}", font=Harmony_Sans_Bold_20, anchor="lm", fill=color)
        # cs, hp, od, ar
        map_diff = [
            beatmap_info.cs,
            beatmap_info.drain,
            beatmap_info.accuracy,
            beatmap_info.ar
        ]
        for i, item in enumerate(map_diff):
            color = (255, 255, 255, 255)
            if i == 4:
                color = (255, 204, 34, 255)
            diff_length = int(250 * item / 10) if item <= 10 else 250
            diff_len = Image.new("RGBA", (diff_length, 8), color)
            im.alpha_composite(diff_len, (890, 426 + 35 * i))
            if i == round(i):
                draw.text(
                    (1170, 428 + 35 * i), "%.1f" % item, font=Harmony_Sans_Bold_20, anchor="mm"
                )
            else:
                draw.text(
                    (1170, 428 + 35 * i), "%.1f" % item, font=Harmony_Sans_Bold_20, anchor="mm"
                )

        # star diff
        star = ss_pp_info.difficulty.stars
        color = (255, 204, 34, 255)
        diff_length = int(250 * star / 10) if star <= 10 else 250
        diff_length_img = Image.new("RGBA", (diff_length, 8), color)
        im.alpha_composite(diff_length_img, (890, 566))
        draw.text((1170, 568), f"{star:.2f}", font=Harmony_Sans_Bold_20, anchor="mm")
        # mapper
        user_icon = await get_user_avatar(mapper_info.id, mapper_info.avatar_url)
        icon = Image.open(BytesIO(user_icon)).convert("RGBA").resize((100, 100))
        icon_img = draw_fillet(icon, 10)
        im.alpha_composite(icon_img, (50, 400))
        # map id
        draw.text(
            (1190, 80),
            f"SET ID: {beatmap_info.beatmapset_id}  |  MAP ID: {beatmap_info.id}",
            font=Harmony_Sans_Bold_20,
            anchor="rm",
        )
        # 难度名
        version = beatmap_info.version
        max_version_length = 60
        if len(version) > max_version_length:
            version = version[:max_version_length - 3] + '...'
        text = f"{version}"
        draw.text((180, 78), text, font=Harmony_Sans_Bold_20, anchor="lm")
        # 曲名+曲师
        text = f"{beatmap_info.beatmapset().title} | by {beatmap_info.beatmapset().artist_unicode}"
        max_length = 80
        if len(text) > max_length:
            text = text[:max_length - 3] + "..."
        draw.text((50, 37), text, font=Harmony_Sans_Bold_20, anchor='lm')
        # 来源
        if beatmap_info.beatmapset().source:
            draw.text((1190, 37), f'Source:{beatmap_info.beatmapset().source}', font=Harmony_Sans_Bold_20, anchor='rm')
        # mapper
        draw.text((160, 400), "谱师:", font=Harmony_Sans_Bold_20, anchor="lt")
        draw.text(
            (160, 425), mapper_info.username, font=Harmony_Sans_Bold_20, anchor="lt"
        )
        # ranked时间
        if beatmap_info.beatmapset().ranked_date:
            new_time = (beatmap_info.beatmapset().ranked_date + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            new_time = "谱面状态非上架"
        draw.text((160, 460), "上架时间:", font=Harmony_Sans_Bold_20, anchor="lt")
        draw.text((160, 485), new_time, font=Harmony_Sans_Bold_20, anchor="lt")
        # 状态
        draw.text(
            (1100, 304), beatmap_info.status.name, font=Harmony_Sans_Bold_20, anchor="mm"
        )
        # 时长 - 滑条
        diff_info = (
            f"{beatmap_info.total_length // 60}:{beatmap_info.total_length % 60:02d}",
            f"{beatmap_info.bpm}",
            f"{beatmap_info.count_circles}",
            f"{beatmap_info.count_sliders}",
        )
        for num, i in enumerate(diff_info):
            draw.text(
                (770 + 120 * num, 365),
                f"{i}",
                font=Harmony_Sans_Bold_20,
                anchor="lm",
                fill=(255, 204, 34, 255),
            )
        # max combo
        draw.text(
            (50, 570), f"最大连击: {beatmap_info.max_combo}", font=Harmony_Sans_Bold_20, anchor="lm"
        )
        # pp
        draw.text(
            (320, 570),
            f"SS PP: {int(round(ss_pp_info.pp, 0))}",
            font=Harmony_Sans_Bold_20,
            anchor="lm",
        )

        byt = BytesIO()
        im.save(byt, "png")
        im.close()

        return byt.getvalue()


def get_theme_strategy():
    return DefaultTheme()
