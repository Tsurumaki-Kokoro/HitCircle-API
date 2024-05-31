from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from app.osu_utils.html_render import html_to_image

MAIN_PATH = Path(__file__).parent


async def draw_bpa_plot(pp_ls, length_ls) -> bytes:
    # 创建一个加载器，Jinja2 会从这个目录中查找模板文件
    file_loader = FileSystemLoader(MAIN_PATH)
    # 创建一个环境，用来管理加载器
    env = Environment(loader=file_loader)
    # 加载模板
    template = env.get_template('bpa_chart.html')
    output = template.render(pp_ls=pp_ls, length_ls=length_ls)
    with open("output.html", "w") as f:
        f.write(output)
    return await html_to_image(output, 900, 550)


async def draw_mod_pp_plot(mod_pp_ls) -> bytes:
    # 创建一个加载器，Jinja2 会从这个目录中查找模板文件
    file_loader = FileSystemLoader(MAIN_PATH)
    # 创建一个环境，用来管理加载器
    env = Environment(loader=file_loader)
    # 加载模板
    template = env.get_template('mod_chart.html')
    output = template.render(mod_pp_ls=mod_pp_ls)
    with open("output.html", "w") as f:
        f.write(output)
    return await html_to_image(output, 450, 300)
