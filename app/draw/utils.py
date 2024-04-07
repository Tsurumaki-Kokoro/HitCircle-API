from PIL import Image, ImageDraw


def crop_image(bg: Image.Image, fix_width: int, fix_height: int) -> Image.Image:
    """
    裁切图片, 保持图片比例
    :param bg: pillow Image 对象
    :param fix_width: 新宽度
    :param fix_height: 新高度
    :return: pillow Image 对象
    """
    bg_w, bg_h = bg.size[0], bg.size[1]
    fix_w, fix_h = fix_width, fix_height
    fix_scale = fix_h / fix_w
    # 图片比例
    bg_scale = bg_h / bg_w
    # 当图片比例大于固定比例
    if bg_scale > fix_scale:
        # 长比例
        scale_width = fix_w / bg_w
        # 等比例缩放
        width = int(scale_width * bg_w)
        height = int(scale_width * bg_h)
        sf = bg.resize((width, height))
        # 计算上下裁切
        crop_height = (height - fix_h) / 2
        x1, y1, x2, y2 = 0, crop_height, width, height - crop_height
        # 裁切保存
        crop_img = sf.crop((x1, int(y1), x2, int(y2)))
        return crop_img
    # 当图片比例小于固定比例
    elif bg_scale < fix_scale:
        # 宽比例
        scale_height = fix_h / bg_h
        # 等比例缩放
        width = int(scale_height * bg_w)
        height = int(scale_height * bg_h)
        sf = bg.resize((width, height))
        # 计算左右裁切
        crop_width = (width - fix_w) / 2
        x1, y1, x2, y2 = crop_width, 0, width - crop_width, height
        # 裁切保存
        crop_img = sf.crop((int(x1), y1, int(x2), y2))
        return crop_img
    else:
        sf = bg.resize((fix_w, fix_h))
        return sf


def draw_fillet(img: Image.Image, radii: int = 20) -> Image.Image:
    """
    处理图片圆角
    :param img: pillow Image 对象
    :param radii: 圆角半径
    :return: pillow Image 对象
    """
    # 画圆（用于分离4个角）
    circle = Image.new("L", (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形
    # 原图
    img = img.convert("RGBA")
    w, h = img.size
    # 画4个角（将整圆分离为4个部分）
    alpha = Image.new("L", img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(
        circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii)
    )  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角
    # 白色区域透明可见，黑色区域不可见
    img.putalpha(alpha)
    return img
