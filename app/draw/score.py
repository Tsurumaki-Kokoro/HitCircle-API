from typing import List

from loguru import logger
from ossapi import User, Score
from ossapi.models import BeatmapDifficultyAttributes

from app.osu_utils.pp import PPCalculator
from app.themes.theme_manager import discover_and_load_themes


class ScoreImageStrategy:
    def __init__(self, present_play_record: List[Score], user_info: User, pp_calculate: PPCalculator,
                 set_bg: bytes, beatmap_attributes: BeatmapDifficultyAttributes) -> None:
        self._themes = discover_and_load_themes('score_image')
        self._present_play_record = present_play_record
        self._user_info = user_info
        self._pp_calculate = pp_calculate
        self._set_bg = set_bg
        self._beatmap_attributes = beatmap_attributes

    async def apply_theme(self, theme_name: str = 'default') -> bytes:
        theme_strategy = self._themes.get(theme_name)
        if not theme_strategy:
            logger.error(f"Theme {theme_name} not found, using default theme")
            theme_strategy = self._themes.get('default')

        try:
            processed_data = await theme_strategy.process_data(
                self._present_play_record, self._user_info, self._pp_calculate, self._set_bg, self._beatmap_attributes
            )
        except Exception as e:
            raise e

        return processed_data
