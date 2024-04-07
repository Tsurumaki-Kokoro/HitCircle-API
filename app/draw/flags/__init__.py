from pathlib import Path

MAIN_PATH = Path(__file__).parent


def get_region_flag(region: str) -> Path:
    region = region.upper()

    return Path(MAIN_PATH / f"{region}.png")
