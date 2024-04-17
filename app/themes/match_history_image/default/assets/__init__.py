from pathlib import Path

MAIN_PATH = Path(__file__).parent

HeaderImg = MAIN_PATH / "other" / "mplink.png"
BodyImg = MAIN_PATH / "other" / "mplink_map.png"
TeamBlue = MAIN_PATH / "other" / "team_blue.png"
TeamRed = MAIN_PATH / "other" / "team_red.png"


def get_mod_image(mod_name: str) -> Path:
    path_name = MAIN_PATH / "mods"
    mod_name = mod_name.upper()

    return Path(path_name / f"{mod_name}.png")
