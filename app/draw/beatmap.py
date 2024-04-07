from loguru import logger
from ossapi.models import Beatmap, Beatmapset, User
from rosu_pp_py import PerformanceAttributes

from app.themes.theme_manager import discover_and_load_themes


class BeatmapImageStrategy:
    def __init__(self, beatmap_info: Beatmap, ss_pp_info: PerformanceAttributes, mapper_info: User, bg_name: str,
                 map_bg: bytes) -> None:
        self._themes = discover_and_load_themes('beatmap_image')
        self._beatmap_info = beatmap_info
        self._ss_pp_info = ss_pp_info
        self._mapper_info = mapper_info
        self._bg_name = bg_name
        self._map_bg = map_bg

    async def apply_theme(self, theme_name: str = 'default') -> bytes:
        theme_strategy = self._themes.get(theme_name)
        if not theme_strategy:
            logger.error(f"Theme {theme_name} not found, using default theme")
            theme_strategy = self._themes.get('default')

        try:
            processed_data = await theme_strategy.process_data(self._beatmap_info, self._ss_pp_info, self._mapper_info,
                                                               self._bg_name, self._map_bg)
        except Exception as e:
            raise e

        return processed_data


class BeatmapSetImageStrategy:
    def __init__(self, beatmap_set_info: Beatmapset) -> None:
        self._themes = discover_and_load_themes('beatmapset_image')
        self._beatmap_set_info = beatmap_set_info

    async def apply_theme(self, theme_name: str = 'default') -> bytes:
        theme_strategy = self._themes.get(theme_name)
        if not theme_strategy:
            logger.error(f"Theme {theme_name} not found, using default theme")
            theme_strategy = self._themes.get('default')

        try:
            processed_data = await theme_strategy.process_data(self._beatmap_set_info)
        except Exception as e:
            raise e

        return processed_data
