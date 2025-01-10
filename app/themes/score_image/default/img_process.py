import math
import numpy as np
from typing import Union
from io import BytesIO
from ossapi import Score

from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
from matplotlib.figure import Figure
from loguru import logger

from app.draw.utils import crop_image
from app.draw.color import ColorArr
from app.themes.score_image.default.assets import MAIN_PATH


def preprocess_bg(bg: Image.Image) -> Image.Image:
    try:
        bg = bg.convert("RGBA")
        cropped_bg = crop_image(bg, 1500, 720)
        cover_gb = cropped_bg.filter(ImageFilter.GaussianBlur(3))
        cover_img = ImageEnhance.Brightness(cover_gb).enhance(2 / 4.0)
        return cover_img
    except Exception as e:
        logger.error(f"Failed to preprocess background: {e}")


def draw_stars_diff(stars: float) -> Image.Image:
    Stars = Image.open(f"{MAIN_PATH}/mode/stars.png")
    if stars < 0.1:
        r, g, b = 170, 170, 170
    elif stars >= 9:
        r, g, b = 0, 0, 0
    else:
        r, g, b, a = ColorArr[int(stars * 100)]
        # 打开底图
    xx, yy = Stars.size
    # 填充背景
    img = Image.new("RGBA", Stars.size, (r, g, b))
    img.paste(Stars, (0, 0, xx, yy), Stars)
    # 把白色变透明
    arr = np.array(img)
    # 创建mask，将白色替换为True，其他颜色替换为False
    mask = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 255) & (arr[:, :, 2] == 255)
    # 将mask中为True的像素点的alpha通道设置为0
    arr[:, :, 3][mask] = 0
    # 将numpy数组转换回PIL图片
    img = Image.fromarray(arr)
    return img


def draw_acc(img: Image.Image, score: Score) -> Image.Image:
    acc = score.accuracy * 100
    mode = score.ruleset_id
    size = [acc, 100 - acc]
    if mode in {0, 4, 8}:
        in_size = [60, 20, 7, 7, 5, 1]
    elif mode in {1, 5}:
        in_size = [60, 20, 5, 5, 4, 1]
    elif mode in {2, 6}:
        in_size = [85, 5, 4, 4, 1, 1]
    else:
        in_size = [70, 10, 10, 5, 4, 1]
    in_size_color = ["#ff5858", "#ea7948", "#d99d03", "#72c904", "#0096a2", "#be0089"]
    fig = Figure()
    ax = fig.add_axes((0.1, 0.1, 0.8, 0.8))
    patches = ax.pie(
        size,
        radius=1,
        startangle=90,
        counterclock=False,
        pctdistance=0.9,
        wedgeprops=dict(width=0.20),
        colors=["#66cbfd"],
    )
    ax.pie(
        in_size,
        radius=0.8,
        colors=in_size_color,
        startangle=90,
        counterclock=False,
        pctdistance=0.9,
        wedgeprops=dict(width=0.05),
    )
    patches[0][1].set_alpha(0)
    acc_img = BytesIO()
    fig.savefig(acc_img, transparent=True)
    ax.cla()
    ax.clear()
    fig.clf()
    fig.clear()
    score_acc_img = Image.open(acc_img).convert("RGBA").resize((576, 432))
    img.alpha_composite(score_acc_img, (25, 83))
    return img
