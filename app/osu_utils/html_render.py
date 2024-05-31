import tempfile
import os

from pyppeteer import launch


async def html_to_image(html_content, width, height):
    # 使用临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
        tmp.write(html_content.encode('utf-8'))
        tmp.flush()  # 确保写入磁盘
        tmp_path = tmp.name

    # 启动浏览器并生成图片
    browser = await launch()
    page = await browser.newPage()
    await page.setViewport({'width': width, 'height': height})
    await page.goto(f'file://{tmp_path}')
    image_bytes = await page.screenshot()
    await browser.close()

    # 清理临时文件
    os.remove(tmp_path)

    return image_bytes

