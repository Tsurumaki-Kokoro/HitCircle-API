from pathlib import Path

MAIN_PATH = Path(__file__).parent

SupporterBadge = MAIN_PATH / "other" / "supporter.png"
IconLs = {"osu": '\uE800', "taiko": '\uE803', "fruits": '\uE801', "mania": '\uE802'}


def get_layout_image(mode: int) -> Path:
    mode = int(mode)
    path_name = MAIN_PATH / "layout"
    if mode == 0:
        return Path(path_name / "std.png")
    elif mode == 1:
        return Path(path_name / "taiko.png")
    elif mode == 2:
        return Path(path_name / "ctb.png")
    elif mode == 3:
        return Path(path_name / "mania.png")
    else:
        return Path(path_name / "std.png")


def get_mod_image(mod_name: str) -> Path:
    path_name = MAIN_PATH / "mods"
    mod_name = mod_name.upper()

    return Path(path_name / f"{mod_name}.png")


def get_rank_image(rank_name: str) -> Path:
    path_name = MAIN_PATH / "rank"
    rank = rank_name.upper()

    return Path(path_name / f"ranking-{rank}.png")
