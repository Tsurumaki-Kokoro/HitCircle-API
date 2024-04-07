import numpy as np
from PIL import Image, ImageEnhance

from app.draw.utils import crop_image
from app.draw.color import ColorArr
from app.themes.beatmap_image.default.assets import MAIN_PATH


async def preprocess_bg(map_bg: Image.Image) -> Image.Image:
    cropped_cover = crop_image(map_bg, 1200, 600)
    final = ImageEnhance.Brightness(cropped_cover).enhance(2 / 4.0)
    return final


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
