from pathlib import Path

MAIN_PATH = Path(__file__).parent

SupporterBadge = MAIN_PATH / "other" / "supporter.png"


def get_exp_bar_image() -> (Path, Path, Path):
    path_name = MAIN_PATH / "other"
    return Path(path_name / "left.png"), Path(path_name / "center.png"), Path(
        path_name / "right.png")


def get_layout_image() -> Path:
    path_name = MAIN_PATH / "layout"
    return Path(path_name / "info_new.png")
