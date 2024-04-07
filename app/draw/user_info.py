from typing import List

from loguru import logger
from ossapi.models import User, Score

from app.themes.theme_manager import discover_and_load_themes
from app.user.models import UserOsuInfoHistory


class UserInfoImageStrategy:
    def __init__(self, user_info: User, user_history_info: UserOsuInfoHistory, game_mode: str,
                 user_scores: List[Score]) -> None:
        self._themes = discover_and_load_themes('user_info_image')
        self._user_info = user_info
        self._user_history_info = user_history_info
        self._game_mode = game_mode
        self._user_scores = user_scores

    async def apply_theme(self, theme_name: str = 'default') -> bytes:
        theme_strategy = self._themes.get(theme_name)
        if not theme_strategy:
            logger.error(f"Theme {theme_name} not found, using default theme")
            theme_strategy = self._themes.get('default')

        try:
            processed_data = await theme_strategy.process_data(self._user_info, self._user_history_info,
                                                               self._game_mode, self._user_scores)
        except Exception as e:
            raise e

        return processed_data
