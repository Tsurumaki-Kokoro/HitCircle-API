from io import BytesIO
from typing import Union

from PIL import Image, ImageDraw, ImageSequence
from ossapi.models import DifficultyAttributes, User, Score, Mod

from app.draw.flags import get_region_flag
from app.osu_utils.beatmap import calculate_circle_size, calculate_hp, calculate_bpm, calculate_length
from app.osu_utils.pp import PPCalculator
from app.osu_utils.user import get_user_avatar
from app.themes.score_image.default.assets import get_layout_image, get_mod_image, get_rank_image, SupporterBadge
from app.draw.fonts import Harmony_Sans_Bold_20, Harmony_Sans_Bold_25, Harmony_Sans_Bold_30, \
    Harmony_Sans_Bold_75, VENERA_75, EXTRA_30
from app.draw.utils import draw_fillet
from app.themes.score_image.default.img_process import preprocess_bg, draw_stars_diff, draw_acc
from app.themes.score_image.default.assets import IconLs
from app.themes.theme_interface import ThemeStrategy


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[Score, User, PPCalculator, bytes, DifficultyAttributes]) -> bytes:
        # 初始化参数
        present_play_record = args[0]
        user_info = args[1]
        pp_calculate = args[2]
        map_bg = Image.open(BytesIO(args[3]))
        difficulty_attributes = args[4].attributes
        # 绘制图像方法
        im = Image.new("RGBA", (1500, 720))
        draw = ImageDraw.Draw(im)
        map_bg = preprocess_bg(map_bg)
        im.alpha_composite(map_bg, (0, 0))
        # 绘制layout
        mode_image_path = get_layout_image(present_play_record.mode_int)
        mode_image = Image.open(mode_image_path).convert("RGBA")
        im.alpha_composite(mode_image, (0, 0))
        # 绘制模式图标
        draw.text((75, 75), IconLs[present_play_record.mode.name.lower()], font=EXTRA_30, anchor="lt")
        # 难度星星
        stars_bg = draw_stars_diff(pp_calculate.pp_info().difficulty.stars)
        stars_img = stars_bg.resize((85, 37))
        im.alpha_composite(stars_img, (122, 72))
        if pp_calculate.pp_info().difficulty.stars < 6.5:
            color = (0, 0, 0, 255)
        else:
            color = (255, 217, 102, 255)
        # 星级
        draw.text((128, 90),
                  f"★{pp_calculate.pp_info().difficulty.stars:.2f}",
                  font=Harmony_Sans_Bold_20,
                  anchor="lm",
                  fill=color
                  )
        # 绘制mod图标
        if present_play_record.mods.short_name() != 'NM':
            for i, mod in enumerate(present_play_record.mods.decompose()):
                mod_img_path = get_mod_image(mod.short_name())
                mod_img = Image.open(mod_img_path).convert("RGBA")
                im.alpha_composite(mod_img, (500 + 50 * i, 160))
        # 绘制rank图标
        if Mod.Hidden in present_play_record.mods.decompose():
            ranking = ["XH", "SH", "A", "B", "C", "D", "F"]
        else:
            ranking = ["X", "S", "A", "B", "C", "D", "F"]

        rank_ok = False
        for rank_num, rank in enumerate(ranking):
            rank_img = get_rank_image(rank)
            if rank_ok:
                rank_b = Image.open(rank_img).convert("RGBA").resize((48, 24))
                rank_new = Image.new("RGBA", rank_b.size, (0, 0, 0, 0))
                rank_bg = Image.blend(rank_new, rank_b, 0.5)
            elif rank != present_play_record.rank.name:
                rank_b = Image.open(rank_img).convert("RGBA").resize((48, 24))
                rank_new = Image.new("RGBA", rank_b.size, (0, 0, 0, 0))
                rank_bg = Image.blend(rank_new, rank_b, 0.2)
            else:
                rank_bg = Image.open(rank_img).convert("RGBA").resize((48, 24))
                rank_ok = True
            im.alpha_composite(rank_bg, (75, 163 + 39 * rank_num))
        # 绘制acc
        im = draw_acc(im, present_play_record)
        # 绘制地区
        region_flag = get_region_flag(user_info.country_code)
        region_img = Image.open(region_flag).convert("RGBA").resize((66, 45))
        im.alpha_composite(region_img, (250, 577))
        # supporter图标
        if user_info.is_supporter:
            supporter_img = Image.open(SupporterBadge).convert("RGBA")
            im.alpha_composite(supporter_img.resize((40, 40)), (250, 640))

        # cs, ar, od, hp
        if present_play_record.mode.name.lower() == "osu":
            map_diff = [
                calculate_circle_size(present_play_record.beatmap.cs, present_play_record.mods.decompose()),
                calculate_hp(present_play_record.beatmap.drain, present_play_record.mods.decompose()),
                difficulty_attributes.overall_difficulty,
                difficulty_attributes.approach_rate,
            ]
        else:
            map_diff = [
                calculate_circle_size(present_play_record.beatmap.cs, present_play_record.mods.decompose()),
                calculate_hp(present_play_record.beatmap.drain, present_play_record.mods.decompose()),
                present_play_record.beatmap.accuracy,
                present_play_record.beatmap.ar,
            ]

        for num, i in enumerate(map_diff):
            if i is None:
                i = 0
            color = (255, 255, 255, 255)
            if num == 4:
                color = (255, 204, 34, 255)
            diff_len = int(250 * i / 10) if i <= 10 else 250
            diff_len = Image.new("RGBA", (diff_len, 8), color)
            im.alpha_composite(diff_len, (1190, 306 + 35 * num))
            if i == round(i):
                draw.text(
                    (1470, 310 + 35 * num), f"{i:.0f}", font=Harmony_Sans_Bold_20, anchor="mm"
                )
            else:
                draw.text(
                    (1470, 310 + 35 * num), f"{i:.1f}", font=Harmony_Sans_Bold_20, anchor="mm"
                )
        # star_rating
        star_rating = pp_calculate.pp_info().difficulty.stars
        color = (255, 204, 34, 255)
        diff_len = max(int(250 * star_rating / 10) if star_rating <= 10 else 250, 0)
        diff_len = Image.new('RGBA', (diff_len, 8), color)
        im.alpha_composite(diff_len, (1190, 446))
        draw.text((1470, 450), f'{star_rating:.2f}', font=Harmony_Sans_Bold_20, anchor='mm')
        # 时长 - 滑条
        diff_info = (
            calculate_length(present_play_record.beatmap.total_length, present_play_record.mods.decompose()),
            calculate_bpm(present_play_record.beatmap.bpm, present_play_record.mods.decompose()),
            present_play_record.beatmap.count_circles,
            present_play_record.beatmap.count_sliders,
        )
        for num, i in enumerate(diff_info):
            draw.text(
                (1070 + 120 * num, 245),
                f"{i}",
                font=Harmony_Sans_Bold_20,
                anchor="lm",
                fill=(255, 204, 34, 255),
            )
        # 谱面状态
        draw.text(
            (1400, 184), present_play_record.beatmap.status.name, font=Harmony_Sans_Bold_20, anchor="mm"
        )
        # map_id
        draw.text((1485, 90), f"MAP ID: {present_play_record.beatmap.id}", font=Harmony_Sans_Bold_25, anchor="rm")
        # 曲名
        draw.text(
            (75, 38),
            f"{present_play_record.beatmap.beatmapset().title} |"
            f" by {present_play_record.beatmap.beatmapset().artist_unicode}",
            font=Harmony_Sans_Bold_30,
            anchor="lm",
        )
        # 谱面版本，mapper
        draw.text(
            (225, 90),
            f"{present_play_record.beatmap.version} | 谱师: {present_play_record.beatmap.beatmapset().creator}",
            font=Harmony_Sans_Bold_20,
            anchor="lm",
        )
        # 评价
        draw.text((316, 307), present_play_record.rank.name, font=VENERA_75, anchor="mm")
        # 分数
        draw.text((498, 251), f"{present_play_record.score:,}", font=Harmony_Sans_Bold_75, anchor="lm")
        # 时间
        draw.text((498, 341), "达成时间:", font=Harmony_Sans_Bold_20, anchor="lm")
        draw.text(
            (630, 341),
            present_play_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            font=Harmony_Sans_Bold_20,
            anchor="lm"
        )
        # 全球排名
        draw.text((583, 410), str(present_play_record.rank_global), font=Harmony_Sans_Bold_25, anchor='mm')
        # 左下玩家名
        draw.text((250, 530), user_info.username, font=Harmony_Sans_Bold_30, anchor="lm")
        # 国内排名
        draw.text(
            (325, 610),
            f"#{user_info.statistics.country_rank:,}",
            font=Harmony_Sans_Bold_25,
            anchor="lm",
        )
        # 右下pp
        if present_play_record.mode.name.lower() == "osu":
            draw.text((720, 550), f"{pp_calculate.if_pp_ss_pp_info()[1]:.0f}", font=Harmony_Sans_Bold_30, anchor="mm")
            draw.text((840, 550), f"{pp_calculate.if_pp_ss_pp_info()[0]:.0f}", font=Harmony_Sans_Bold_30, anchor="mm")
            draw.text((960, 550), f"{pp_calculate.pp_info().pp:.0f}", font=Harmony_Sans_Bold_30, anchor="mm")
            draw.text(
                (720, 645), f"{pp_calculate.pp_info().pp_aim:.0f}", font=Harmony_Sans_Bold_30, anchor="mm"
            )
            draw.text(
                (840, 645), f"{pp_calculate.pp_info().pp_speed:.0f}", font=Harmony_Sans_Bold_30, anchor="mm"
            )
            draw.text(
                (960, 645), f"{pp_calculate.pp_info().pp_accuracy:.0f}", font=Harmony_Sans_Bold_30, anchor="mm"
            )
            draw.text(
                (1157, 550),
                f"{present_play_record.accuracy * 100:.2f}%",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1385, 550),
                f"{present_play_record.max_combo:,}/{difficulty_attributes.max_combo:,}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1100, 645),
                f"{present_play_record.statistics.count_300}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1214, 645),
                f"{present_play_record.statistics.count_100}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1328, 645),
                f"{present_play_record.statistics.count_50}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1442, 645),
                f"{present_play_record.statistics.count_miss}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
        elif present_play_record.mode.name.lower() == "taiko":
            draw.text(
                (1118, 550),
                f"{present_play_record.accuracy * 100:.2f}%",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1270, 550), f"{present_play_record.max_combo:,}", font=Harmony_Sans_Bold_30, anchor="mm"
            )
            draw.text(
                (1420, 550),
                f"{pp_calculate.pp_info().pp:.0f}/{pp_calculate.if_pp_ss_pp_info()[1]:.0f}",
                font=Harmony_Sans_Bold_30,
                anchor="mm"
            )
            draw.text(
                (1118, 645),
                f"{present_play_record.statistics.count_300}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1270, 645),
                f"{present_play_record.statistics.count_100}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1420, 645),
                f"{present_play_record.statistics.count_miss}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
        elif present_play_record.mode.name.lower() == "catch":
            draw.text(
                (1083, 550),
                f"{present_play_record.accuracy * 100:.2f}%",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1247, 550),
                f"{present_play_record.max_combo:,}/{difficulty_attributes.max_combo:,}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1411, 550),
                f"{pp_calculate.pp_info().pp:.0f}/{pp_calculate.if_pp_ss_pp_info()[1]:.0f}",
                font=Harmony_Sans_Bold_30,
                anchor="mm"
            )
            draw.text(
                (1062, 645),
                f"{present_play_record.statistics.count_300}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1185, 645),
                f"{present_play_record.statistics.count_100}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1309, 645),
                f"{present_play_record.statistics.count_katu}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1432, 645),
                f"{present_play_record.statistics.count_miss}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
        else:
            draw.text(
                (1002, 580),
                f"{present_play_record.statistics.count_geki / present_play_record.statistics.count_300 :.1f}:1"
                if present_play_record.statistics.count_300 != 0
                else "∞:1",
                font=Harmony_Sans_Bold_20,
                anchor="mm",
            )
            draw.text(
                (1002, 550),
                f"{present_play_record.accuracy * 100:.2f}%",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1197, 550), f"{present_play_record.max_combo:,}", font=Harmony_Sans_Bold_30, anchor="mm"
            )
            draw.text(
                (1395, 550),
                f"{pp_calculate.pp_info().pp:.0f}/{pp_calculate.if_pp_ss_pp_info()[1]:.0f}",
                font=Harmony_Sans_Bold_30,
                anchor="mm"
            )
            draw.text(
                (953, 645),
                f"{present_play_record.statistics.count_geki}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1051, 645),
                f"{present_play_record.statistics.count_300}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1150, 645),
                f"{present_play_record.statistics.count_katu}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1249, 645),
                f"{present_play_record.statistics.count_100}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1347, 645),
                f"{present_play_record.statistics.count_50}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )
            draw.text(
                (1445, 645),
                f"{present_play_record.statistics.count_miss}",
                font=Harmony_Sans_Bold_30,
                anchor="mm",
            )

        user_icon = await get_user_avatar(user_info.id, user_info.avatar_url)
        user_icon = Image.open(BytesIO(user_icon)).convert("RGBA")
        gif_frames = []
        if not getattr(user_icon, "is_animated", False):
            icon_bg = user_icon.convert("RGBA").resize((170, 170))
            icon_img = draw_fillet(icon_bg, 15)
            im.alpha_composite(icon_img, (60, 510))
            byt = BytesIO()
            im.save(byt, "png")
            im.close()
            user_icon.close()
            return byt.getvalue()
        for gif_frame in ImageSequence.Iterator(user_icon):
            # 将 GIF 图片中的每一帧转换为 RGBA 模式
            gif_frame = gif_frame.convert("RGBA").resize((170, 170))
            gif_frame = draw_fillet(gif_frame, 15)
            # 创建一个新的 RGBA 图片，将 PNG 图片作为背景，将当前帧添加到背景上
            rgba_frame = Image.new("RGBA", im.size, (0, 0, 0, 0))
            rgba_frame.paste(im, (0, 0), im)
            rgba_frame.paste(gif_frame, (60, 510), gif_frame)
            # 将 RGBA 图片转换为 RGB 模式，并添加到 GIF 图片中
            gif_frames.append(rgba_frame)
        # 保存图像
        gif_bytes = BytesIO()
        # 保存 GIF 图片
        gif_frames[0].save(
            gif_bytes, format="gif", save_all=True, append_images=gif_frames[1:]
        )
        # 输出
        gif_frames[0].close()
        user_icon.close()
        return gif_bytes.getvalue()


def get_theme_strategy():
    return DefaultTheme()
