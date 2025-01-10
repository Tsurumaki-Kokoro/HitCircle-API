from pathlib import Path

MAIN_PATH = Path(__file__).parent

SupporterBadge = MAIN_PATH / "other" / "supporter.png"
# IconLs = {"osu": '\uE800', "taiko": '\uE803', "fruits": '\uE801', "mania": '\uE802'}
IconLs = ["\ue800", "\ue803", "\ue801", "\ue802", "\ue800", "\ue803", "\ue801", "\ue802", "\ue800"]


def get_layout_image(ruleset_id: int) -> Path:
    path_name = MAIN_PATH / "layout"
    if ruleset_id in {0, 4, 8}:
        return Path(path_name / "std.png")
    elif ruleset_id in {1, 5}:
        return Path(path_name / "taiko.png")
    elif ruleset_id in {2, 6}:
        return Path(path_name / "ctb.png")
    elif ruleset_id in {3, 7}:
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
