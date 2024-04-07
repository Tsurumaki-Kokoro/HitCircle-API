import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from loguru import logger

from app.draw.color import ColorArr
from app.draw.utils import crop_image
from app.themes.beatmapset_image.default.assets import MAIN_PATH


def preprocess_bg(bg: Image.Image) -> Image.Image:
    try:
        bg = bg.convert("RGBA")
        cropped_bg = crop_image(bg, 1200, 300)
        cover_gb = cropped_bg.filter(ImageFilter.GaussianBlur(1))
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
