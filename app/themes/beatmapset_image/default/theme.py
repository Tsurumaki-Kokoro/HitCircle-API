from datetime import timedelta
from io import BytesIO
from typing import Union

from PIL import Image, ImageDraw
from ossapi.models import Beatmapset

from app.draw.fonts import (Harmony_Sans_Bold_40, Harmony_Sans_Bold_50, Harmony_Sans_Bold_20, Harmony_Sans_Bold_15, EXTRA_30)
from app.osu_utils.beatmap import get_map_bg
from app.themes.beatmapset_image.default.assets import BarImg, IconLs
from app.themes.beatmapset_image.default.img_process import preprocess_bg, draw_stars_diff
from app.themes.theme_interface import ThemeStrategy


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[Beatmapset]) -> bytes:
        # 初始化参数
        beatmapset_info = args[0]
        # 新建画布
        if len(beatmapset_info.beatmaps) > 20:
            img_height = 400 + 102 * 20
        else:
            img_height = 400 + 102 * (len(beatmapset_info.beatmaps) - 1)
        im = Image.new("RGBA", (1200, img_height), (31, 41, 46, 255))
        draw = ImageDraw.Draw(im)
        # 背景
        cover = await get_map_bg(set_id=beatmapset_info.id)
        cover = Image.open(BytesIO(cover))
        cover_img = preprocess_bg(cover)
        im.alpha_composite(cover_img, (0, 0))
        # 曲名
        draw.text((25, 15), beatmapset_info.title, font=Harmony_Sans_Bold_40, anchor="lt")
        # 曲师
        draw.text((25, 70), f"by {beatmapset_info.artist}", font=Harmony_Sans_Bold_20, anchor="lt")
        # mapper
        draw.text((25, 105), f"谱面作者: {beatmapset_info.creator}", font=Harmony_Sans_Bold_20, anchor="lt")
        # rank时间
        if beatmapset_info.ranked_date is None:
            approved_date = "谱面状态可能非ranked"
        else:
            approved_date = (beatmapset_info.ranked_date + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        draw.text((25, 140), f"上架时间: {approved_date}", font=Harmony_Sans_Bold_20, anchor="lt")
        # 来源
        draw.text((25, 175), f"Source: {beatmapset_info.source}", font=Harmony_Sans_Bold_20, anchor="lt")
        # bpm
        draw.text((1150, 105), f"BPM: {beatmapset_info.bpm}", font=Harmony_Sans_Bold_20, anchor="rt")
        # 曲长
        music_len = (f"{int(beatmapset_info.beatmaps[0].hit_length / 60)}"
                     f":{beatmapset_info.beatmaps[0].hit_length % 60:02d}")
        draw.text((1150, 140), f"Hit Length: {music_len}", font=Harmony_Sans_Bold_20, anchor="rt")
        # Set id
        draw.text((1150, 70), f"SET ID: {beatmapset_info.id}", font=Harmony_Sans_Bold_20, anchor="rt")
        gmap = sorted(beatmapset_info.beatmaps, key=lambda k: k.difficulty_rating, reverse=False)
        for num, item in enumerate(gmap):
            if num < 20:
                h_num = 102 * num
                # 难度
                draw.text((20, 320 + h_num), IconLs[item.mode.name.lower()], font=EXTRA_30, anchor="lt")
                # 星星
                stars_bg = draw_stars_diff(item.difficulty_rating)
                stars_img = stars_bg.resize((80, 30))
                im.alpha_composite(stars_img, (60, 320 + h_num))
                # diff
                im.alpha_composite(Image.open(str(BarImg)), (10, 365 + h_num))
                gc = ["CS", "HP", "OD", "AR"]
                for index, i in enumerate((item.cs, item.drain, item.accuracy, item.ar)):
                    diff_len = int(200 * i / 10) if i <= 10 else 200
                    diff_bg = Image.new("RGBA", (diff_len, 12), (255, 255, 255, 255))
                    im.alpha_composite(diff_bg, (50 + 300 * index, 365 + h_num))
                    draw.text(
                        (20 + 300 * index, 371 + h_num),
                        gc[index],
                        font=Harmony_Sans_Bold_15,
                        anchor="lm",
                    )
                    draw.text(
                        (265 + 300 * index, 371 + h_num),
                        f"{i}",
                        font=Harmony_Sans_Bold_15,
                        anchor="lm",
                        fill=(255, 204, 34, 255),
                    )
                    if index != 3:
                        draw.text(
                            (300 + 300 * index, 371 + h_num),
                            "|",
                            font=Harmony_Sans_Bold_15,
                            anchor="lm",
                        )
                # 难度
                if item.difficulty_rating < 6.5:
                    color = (0, 0, 0, 255)
                else:
                    color = (255, 217, 102, 255)
                draw.text(
                    (100, 335 + h_num),
                    f"{item.difficulty_rating:.2f}",
                    font=Harmony_Sans_Bold_20,
                    anchor="mm",
                    fill=color,
                )
                # version
                draw.text(
                    (150, 335 + h_num),
                    f" |  {item.version}",
                    font=Harmony_Sans_Bold_20,
                    anchor="lm",
                )
                # map id
                draw.text(
                    (1150, 332 + h_num),
                    f"MAP ID: {item.id}",
                    font=Harmony_Sans_Bold_15,
                    anchor="rm",
                )
                # max combo
                draw.text(
                    (700, 332 + h_num),
                    f"Max Combo: {item.max_combo}",
                    font=Harmony_Sans_Bold_15,
                    anchor="lm",
                )
                # 分割线
                div = Image.new("RGBA", (1150, 2), (46, 53, 56, 255)).convert("RGBA")
                im.alpha_composite(div, (25, 400 + h_num))
            else:
                plus_num = f"+ {num - 19}"
                draw.text(
                    (600, 350 + 102 * 20), plus_num, font=Harmony_Sans_Bold_50, anchor="mm"
                )

        byt = BytesIO()
        im.save(byt, format="PNG")
        im.close()

        return byt.getvalue()


def get_theme_strategy():
    return DefaultTheme()
