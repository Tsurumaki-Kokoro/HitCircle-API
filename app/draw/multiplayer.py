from loguru import logger
from ossapi.models import MatchResponse

from app.themes.theme_manager import discover_and_load_themes


class MatchHistoryImageStrategy:
    def __init__(self, match_record: MatchResponse) -> None:
        self._themes = discover_and_load_themes('match_history_image')
        self._match_record = match_record

    async def apply_theme(self, theme_name: str = 'default') -> bytes:
        theme_strategy = self._themes.get(theme_name)
        if not theme_strategy:
            logger.error(f"Theme {theme_name} not found, using default theme")
            theme_strategy = self._themes.get('default')

        try:
            processed_data = await theme_strategy.process_data(
                self._match_record
            )
        except Exception as e:
            raise e

        return processed_data


class RatingImageStrategy:
    def __init__(self, match_record: MatchResponse, algorithm: str) -> None:
        self._themes = discover_and_load_themes('rating_image')
        self._match_record = match_record
        self._algorithm = algorithm

    async def apply_theme(self, theme_name: str = 'default') -> bytes:
        theme_strategy = self._themes.get(theme_name)
        if not theme_strategy:
            logger.error(f"Theme {theme_name} not found, using default theme")
            theme_strategy = self._themes.get('default')

        try:
            processed_data = await theme_strategy.process_data(
                self._match_record, self._algorithm
            )
        except Exception as e:
            raise e

        return processed_data

