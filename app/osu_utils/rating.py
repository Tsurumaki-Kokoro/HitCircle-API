from collections import Counter
from typing import List
from statistics import median

from ossapi.models import MatchResponse, MatchEventType, MatchGame

from app.osu_utils.multiplayer import get_win_side


class PlayerRatingCalculation:
    def __init__(self, match_info: MatchResponse):
        self._match_info = match_info

    def get_rating(self, user_id: int, algorithm: str = "osuplus"):
        if algorithm == "osuplus":
            return self._osuplus_rating(user_id)
        if algorithm == "bathbot":
            return self._bathbot_rating(user_id)
        if algorithm == "flashlight":
            return self._flashlight_rating(user_id)

        return None

    def _osuplus_rating(self, user_id: int) -> float:
        # 获取比赛中的所有记录
        game_history = []
        for sequence in self._match_info.events:
            if sequence.detail.type == MatchEventType.OTHER and sequence.game is not None:
                game_history.append(sequence.game)

        # 统计比赛中的数据
        number_of_games = 0
        number_of_games_by_user = 0
        user_scores = []
        average_scores = []

        for i, game in enumerate(game_history):
            if len(game.scores) == 0:
                continue
            number_of_games += 1
            for entry in game.scores:
                user_info = next(
                    (user for user in self._match_info.users if user.id == user_id), (None, None, None)
                )
                if user_info is None:
                    continue
                if entry.user_id == user_id:
                    average_scores.append(sum([entry.score for entry in game.scores]) / len(game.scores))
                    user_scores.append(entry.score)
                    number_of_games_by_user += 1

        # 计算osuplus算法评分
        n_prime = len(user_scores)  # number of games by the player
        sum_of_ratios = sum(s_i / m_i for s_i, m_i in zip(user_scores, average_scores) if m_i != 0)
        cost = (2 / (n_prime + 2)) * sum_of_ratios

        return cost

    def _bathbot_rating(self, user_id: int) -> float:
        # 获取比赛中的所有记录
        game_history = []
        for sequence in self._match_info.events:
            if sequence.detail.type == MatchEventType.OTHER and sequence.game is not None:
                game_history.append(sequence.game)

        number_of_games = 0
        number_of_games_by_user = 0
        user_tiebreaker_score = 0
        average_tiebreaker_score = 0
        user_scores = []
        average_scores = []
        red_score = 0
        blue_score = 0
        tiebreaker = False
        all_played_mods = set()

        for i, game in enumerate(game_history):
            if len(game.scores) == 0:
                continue
            number_of_games += 1
            # 获取比分
            win_side = get_win_side(game)
            if win_side == "red":
                red_score += 1
            elif win_side == "blue":
                blue_score += 1
            for entry in game.scores:
                user_info = next(
                    (user for user in self._match_info.users if user.id == user_id), (None, None, None)
                )
                if user_info is None:
                    continue
                if entry.user_id == user_id:
                    for mod in entry.mods:
                        all_played_mods.add(mod.acronym)
                    average_scores.append(sum([entry.score for entry in game.scores]) / len(game.scores))
                    user_scores.append(entry.score)
                    number_of_games_by_user += 1
            # 获取加时赛数据
            if i == len(game_history) - 2 and red_score == blue_score:
                tiebreaker = True
                average_tiebreaker_score = sum(entry.score for entry in game.scores) / len(game.scores)
                for entry in game.scores:
                    if entry.user_id == user_id:
                        user_tiebreaker_score = entry.score
                        break

        # 计算bathbot算法评分
        score_sum = sum(player_score / avg_score for player_score, avg_score in zip(user_scores, average_scores))
        participation_bonus = number_of_games_by_user * 0.5
        if tiebreaker:
            tiebreaker_bonus = user_tiebreaker_score / average_tiebreaker_score
        else:
            tiebreaker_bonus = 0
        average_factor = 1 / number_of_games_by_user
        participation_bonus_factor = 1.4 ** ((number_of_games_by_user - 1) / (number_of_games - 1)) ** 0.6
        mod_combination_bonus_factor = 1 + 0.02 * max(0, len(all_played_mods) - 2)
        rating = ((score_sum + participation_bonus + tiebreaker_bonus) * average_factor *
                  participation_bonus_factor * mod_combination_bonus_factor)

        return rating

    def _flashlight_rating(self, user_id: int) -> float:
        # 获取比赛中的所有记录
        game_history = []
        for sequence in self._match_info.events:
            if sequence.detail.type == MatchEventType.OTHER and sequence.game is not None:
                game_history.append(sequence.game)

        # 统计比赛中的数据
        number_of_games_by_user = 0
        user_scores = []
        median_scores = []
        counts = Counter()

        for i, game in enumerate(game_history):
            if len(game.scores) == 0:
                continue

            for entry in game.scores:
                counts[entry.user_id] += 1
                user_info = next(
                    (user for user in self._match_info.users if user.id == user_id), (None, None, None)
                )
                if user_info is None:
                    continue
                if entry.user_id == user_id:
                    median_scores.append(median([entry.score for entry in game.scores]))
                    user_scores.append(entry.score)
                    number_of_games_by_user += 1

        # 计算中位数
        occurrences = sorted(counts.values(), reverse=True)
        median_of_games_of_all_users = median(occurrences)

        # 计算flashlight算法评分
        sum_of_ratios = sum(N_i / M_i for N_i, M_i in zip(user_scores, median_scores))
        average_ratio = sum_of_ratios / number_of_games_by_user
        adjustment_factor = (number_of_games_by_user / median_of_games_of_all_users) ** (1 / 3)
        match_costs = average_ratio * adjustment_factor

        return match_costs
