import numpy as np
from PIL import Image, ImageEnhance
from loguru import logger

from ossapi.models import MatchGame, Score

from app.themes.match_history_image.default.assets import MAIN_PATH
from app.draw.color import ColorArr
from app.draw.utils import crop_image, draw_fillet


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


def preprocess_bg(bg: Image.Image) -> Image.Image:
    try:
        bg = bg.convert("RGBA")
        cropped_bg = crop_image(bg, 240, 120)
        rounded_bg = draw_fillet(cropped_bg, 20)
        enhanced_bg = ImageEnhance.Brightness(rounded_bg).enhance(0.5)
        return enhanced_bg
    except Exception as e:
        logger.error(f"Failed to preprocess background: {e}")


def get_score_diff(game: MatchGame) -> int:
    scores = game.scores
    total_score_red = 0
    total_score_blue = 0

    for entry in scores:
        if entry.match.team == "red":
            total_score_red += entry.score
        elif entry.match.team == "blue":
            total_score_blue += entry.score

    score_diff = total_score_red - total_score_blue
    return abs(score_diff)


def get_top3(scores: list[Score]) -> list:
    top3 = []
    for entry in scores:
        top3.append((entry.user_id, entry.score))
    top3 = sorted(top3, key=lambda x: x[1], reverse=True)
    return top3[:3]


def get_top3_color(value: int) -> str:
    if value == 1:
        return "gold"
    elif value == 2:
        return "silver"
    elif value == 3:
        return "#cd7f32"
    else:
        return "white"
