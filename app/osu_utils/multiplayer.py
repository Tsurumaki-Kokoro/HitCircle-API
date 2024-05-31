from statistics import mode
from typing import List

from fastapi import HTTPException, Response
from loguru import logger
from ossapi import MatchGame

from ossapi.models import MatchEventType, UserCompact

from app.config.settings import osu_api
from app.draw.multiplayer import MatchHistoryImageStrategy, RatingImageStrategy


async def generate_match_history_img(mp_id: int, theme: str = "default"):
    match_info = osu_api.match(mp_id)
    if not match_info:
        raise HTTPException(status_code=404, detail="No match found")

    while match_info.events[0].detail.type != MatchEventType.MATCH_CREATED:
        logger.debug(f"Match Created not found, trying to get previous events")
        before_match_info = osu_api.match(match_id=mp_id, before_id=match_info.events[0].id)
        if not before_match_info:
            raise HTTPException(status_code=404, detail="No match found")
        match_info.events = before_match_info.events + match_info.events

    try:
        illustration = MatchHistoryImageStrategy(match_info)
        image = await illustration.apply_theme(theme)
    except Exception as e:
        logger.error(f"Error when drawing image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")


async def generate_rating_img(mp_id: int, algorithm: str, theme: str = "default"):
    match_info = osu_api.match(mp_id)
    if not match_info:
        raise HTTPException(status_code=404, detail="No match found")

    while match_info.events[0].detail.type != MatchEventType.MATCH_CREATED:
        logger.debug(f"Match Created not found, trying to get previous events")
        before_match_info = osu_api.match(match_id=mp_id, before_id=match_info.events[0].id)
        if not before_match_info:
            raise HTTPException(status_code=404, detail="No match found")
        match_info.events = before_match_info.events + match_info.events

    try:
        illustration = RatingImageStrategy(match_info, algorithm)
        image = await illustration.apply_theme(theme)
    except Exception as e:
        logger.error(f"Error when drawing image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return Response(content=image, media_type="image/jpeg")


class PlayerMatchStats:
    def __init__(self, user: UserCompact, game_history: List[MatchGame]):
        self.user = user
        self.game_history = game_history
        self.player_team = self._get_player_team()
        self.win_and_lose = self._get_win_and_lose()
        self.win_rate = self._get_win_rate()
        self.total_score = self._get_total_score()
        self.average_score = self._get_average_score()

    def _get_player_team(self) -> str:
        """
        获取用户所在队伍
        :return: 队伍
        """
        for game in self.game_history:
            for entry in game.scores:
                if entry.user_id == self.user.id:
                    return entry.match.team

    def _get_win_and_lose(self) -> tuple:
        """
        获取用户胜利和失败次数
        :return: (胜利次数, 失败次数)
        """
        number_of_wins_by_user = 0
        number_of_games_by_user = 0

        for i, game in enumerate(self.game_history):
            if len(game.scores) == 0:
                continue
            for entry in game.scores:
                if entry.user_id == self.user.id:
                    number_of_games_by_user += 1
                    player_team = entry.match.team
                    win_side = get_win_side(game)
                    if player_team == win_side:
                        number_of_wins_by_user += 1

        number_of_loses_by_user = number_of_games_by_user - number_of_wins_by_user
        return number_of_wins_by_user, number_of_loses_by_user, number_of_games_by_user

    def _get_win_rate(self) -> float:
        """
        获取用户胜率
        :return: 胜率
        """
        number_of_wins_by_user = 0
        number_of_games_by_user = 0

        for i, game in enumerate(self.game_history):
            if len(game.scores) == 0:
                continue
            for entry in game.scores:
                if entry.user_id == self.user.id:
                    number_of_games_by_user += 1
                    player_team = entry.match.team
                    win_side = get_win_side(game)
                    if player_team == win_side:
                        number_of_wins_by_user += 1

        if number_of_games_by_user == 0:
            return 0
        win_rate = number_of_wins_by_user / number_of_games_by_user
        return win_rate

    def _get_total_score(self) -> int:
        """
        获取用户总分数
        :return: 总分数
        """
        total_score = 0
        for game in self.game_history:
            for entry in game.scores:
                if entry.user_id == self.user.id:
                    total_score += entry.score
        return total_score

    def _get_average_score(self) -> float:
        """
        获取用户平均分数
        :return: 平均分数
        """
        total_score = 0
        number_of_games = 0
        for game in self.game_history:
            for entry in game.scores:
                if entry.user_id == self.user.id:
                    total_score += entry.score
                    number_of_games += 1
        if number_of_games == 0:
            return 0
        average_score = total_score / number_of_games
        return average_score


def analyze_team_vs_game_history(game_history: List[MatchGame]) -> dict:
    red_score = 0
    blue_score = 0
    team_size_list = []
    for game in game_history:
        # 获取比分
        win_side = get_win_side(game)
        if win_side == "red":
            red_score += 1
        elif win_side == "blue":
            blue_score += 1
        # 获取队伍大小
        team_red_size = 0
        team_blue_size = 0
        for entry in game.scores:
            if entry.score == 0:
                continue
            if entry.match.team == "red":
                team_red_size += 1
            elif entry.match.team == "blue":
                team_blue_size += 1
        if team_red_size == team_blue_size and team_red_size != 0:
            team_size_list.append(team_red_size)

    analyze_result = {
        "red_score": red_score,
        "blue_score": blue_score,
        "team_size": mode(team_size_list)  # 从 TeamSize 中获取众数, 即队伍大小
    }
    return analyze_result


def analyze_head_to_head_history(game_history: List[MatchGame], user_id: int) -> dict:
    number_of_games = 0
    number_of_games_top1 = 0
    # 获取用户上场次数
    for i, game in enumerate(game_history):
        if len(game.scores) == 0:
            continue
        max_score_obj = max(game.scores, key=lambda x: x.score)
        for entry in game.scores:
            if entry.user_id == user_id:
                number_of_games += 1
        if max_score_obj.user_id == user_id:
            number_of_games_top1 += 1

    analyze_result = {
        "number_of_games": number_of_games,
        "number_of_games_top1": number_of_games_top1,
        "top1_rate": number_of_games_top1 / number_of_games if number_of_games != 0 else 0
    }
    return analyze_result


def get_win_side(game: MatchGame) -> str:
    scores = game.scores
    total_score_red = 0
    total_score_blue = 0

    for entry in scores:
        if entry.match.team == "red":
            total_score_red += entry.score
        elif entry.match.team == "blue":
            total_score_blue += entry.score

    if total_score_red > total_score_blue:
        win_side = "red"
    else:
        win_side = "blue"

    return win_side
