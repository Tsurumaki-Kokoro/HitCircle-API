from collections import defaultdict
from datetime import datetime
from io import BytesIO
from typing import Union, List

from PIL import Image, ImageDraw
from ossapi.models import User, Score, Grade
from ossapi import Mod

from app.config.settings import osu_api
from app.draw.fonts import *
from app.themes.theme_interface import ThemeStrategy
from app.themes.bp_analyze_image.default.templates import draw_bpa_plot, draw_mod_pp_plot


class DefaultTheme(ThemeStrategy):
    async def process_data(self, *args: Union[User, List[Score]]) -> bytes:
        user_info = args[0]
        user_scores = args[1]

        for score in user_scores:
            if Mod.DT in score.mods or Mod.NC in score.mods:
                score.beatmap.total_length /= 1.5
            if Mod.HT in score.mods:
                score.beatmap.total_length /= 0.75
        pp_ls = [round(i.pp, 0) for i in user_scores]
        length_ls = []
        for i in user_scores:
            if i.rank == "XH":
                length_ls.append({'value': i.beatmap.total_length,
                                  'itemStyle': {'color': rank_color[i.rank], 'shadowBlur': 8,
                                                'shadowColor': "#b4ffff"}})
            elif i.rank == "X":
                length_ls.append({'value': i.beatmap.total_length,
                                  'itemStyle': {'color': rank_color[i.rank], 'shadowBlur': 8,
                                                'shadowColor': "#ffff00"}})
            else:
                length_ls.append({'value': i.beatmap.total_length, 'itemStyle': {'color': rank_color[i.rank]}})

        img1 = await draw_bpa_plot(pp_ls, length_ls)

        mods_pp = defaultdict(int)
        for num, i in enumerate(user_scores):
            if i.mods == Mod.NM:
                mods_pp["NM"] += i.pp * 0.95 ** num
            else:
                for j in i.mods.decompose():
                    mods_pp[j.short_name()] += i.pp * 0.95 ** num
        pp_data = []
        for mod, pp in mods_pp.items():
            pp_data.append({'name': mod, 'value': round(pp, 2)})

        img2 = await draw_mod_pp_plot(pp_data)

        mapper_pp = defaultdict(int)
        for num, i in enumerate(user_scores):
            mapper_pp[i.beatmap.user_id] += i.pp * 0.95 ** num
        mapper_pp = sorted(mapper_pp.items(), key=lambda x: x[1], reverse=True)
        mapper_pp = mapper_pp[: 10]
        users = []
        for i in mapper_pp:
            try:
                users.append(osu_api.user(i[0], mode="osu", key="id"))
            except ValueError:
                continue
        user_dic = {i.id: i.username for i in users}
        mapper_pp_data = []
        for mapper, pp in mapper_pp:
            mapper_pp_data.append({'name': user_dic.get(mapper, ''), 'value': round(pp, 2)})
        if len(mapper_pp_data) > 20:
            mapper_pp_data = mapper_pp_data[: 20]

        img3 = await draw_mod_pp_plot(mapper_pp_data)

        im = Image.new("RGBA", (950, 950), (255, 255, 255, 255))
        draw = ImageDraw.Draw(im)
        im.paste(Image.open(BytesIO(img1)).convert("RGBA"), (0, 50))
        im.paste(Image.open(BytesIO(img2)).convert("RGBA"), (0, 600))
        im.paste(Image.open(BytesIO(img3)).convert("RGBA"), (450, 600))
        draw.text((945, 950), f"绘制时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                  font=Harmony_Sans_Reg_15, fill="gray", anchor="rb")
        draw.text((945, 930), f"Powered by HitCircle API", font=Harmony_Sans_Reg_15, fill="gray", anchor="rb")
        draw.text((450, 5), f"{user_info.username}的bp分析", font=Harmony_Sans_Bold_40, fill="gray", anchor="mt")
        draw.text((40, 570), "mod分布", font=Harmony_Sans_Bold_25, fill="gray")
        draw.text((490, 570), "mapper分布", font=Harmony_Sans_Bold_25, fill="gray")

        byt = BytesIO()
        im.save(byt, format="PNG")
        im.close()

        return byt.getvalue()


def get_theme_strategy():
    return DefaultTheme()


rank_color = {
    Grade.SS: "#ffc83a",
    Grade.SSH: "#c7eaf5",
    Grade.S: "#ffc83a",
    Grade.SH: "#c7eaf5",
    Grade.A: "#84d61c",
    Grade.B: "#e9b941",
    Grade.C: "#fa8a59",
    Grade.D: "#f55757",
}
