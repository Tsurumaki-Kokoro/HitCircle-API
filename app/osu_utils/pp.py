import math
import numpy as np
from pathlib import Path

from ossapi import Score
from rosu_pp_py import PerformanceAttributes, Beatmap, Performance, GameMode


class PPCalculator:
    """
    PP计算器
    """

    def __init__(self, score: Score, osu_file_path: Path):
        """
        :param score:
        :param osu_file_path:
        """
        self.score = score
        self.osu_file_path = osu_file_path

    def pp_info(self) -> PerformanceAttributes:
        """
        计算pp
        :return:
        """
        beatmap = Beatmap(path=str(self.osu_file_path))
        mods = [item.acronym for item in self.score.mods]
        if self.score.ruleset_id in {0, 4, 8}:
            mode = GameMode.Osu
        elif self.score.ruleset_id in {1, 5}:
            mode = GameMode.Taiko
        elif self.score.ruleset_id in {2, 6}:
            mode = GameMode.Catch
        else:
            mode = GameMode.Mania
        beatmap.convert(mode, mods=mods)

        c = Performance(
            accuracy=self.score.accuracy * 100,
            n_katu=self.score.statistics.good if self.score.statistics.good else 0,
            n_geki=self.score.statistics.perfect if self.score.statistics.perfect else 0,
            combo=self.score.max_combo,
            misses=self.score.statistics.miss if self.score.statistics.miss else 0,
            n50=self.score.statistics.meh if self.score.statistics.meh else 0,
            n100=self.score.statistics.ok if self.score.statistics.ok else 0,
            n300=self.score.statistics.great if self.score.statistics.great else 0,
            small_tick_hits=self.score.statistics.small_tick_hit,
            large_tick_hits=self.score.statistics.large_tick_hit,
            slider_end_hits=self.score.statistics.slider_tail_hit,
            mods=mods,
        )

        return c.calculate(beatmap)

    def if_pp_ss_pp_info(self) -> tuple[float, float] | tuple[str, str]:
        """
        获取 if fc pp 和 ss pp
        :return: if pp 和 ss pp
        """
        beatmap = Beatmap(path=str(self.osu_file_path))
        mods = [item.acronym for item in self.score.mods]
        if self.score.ruleset_id in {0, 4, 8}:
            mode = GameMode.Osu
        elif self.score.ruleset_id in {1, 5}:
            mode = GameMode.Taiko
        elif self.score.ruleset_id in {2, 6}:
            mode = GameMode.Catch
        else:
            mode = GameMode.Mania
        beatmap.convert(mode, mods=mods)
        c = Performance(
            accuracy=self.score.accuracy * 100,
            n_katu=self.score.statistics.good if self.score.statistics.good else 0,
            n_geki=self.score.statistics.perfect if self.score.statistics.perfect else 0,
            n50=self.score.statistics.meh if self.score.statistics.meh else 0,
            n100=self.score.statistics.ok if self.score.statistics.ok else 0,
            n300=self.score.statistics.great + (self.score.statistics.miss if self.score.statistics.miss else 0),
            mods=mods,
        )
        if_pp = c.calculate(beatmap).pp
        c = Performance(accuracy=100, mods=mods)
        ss_pp = c.calculate(beatmap).pp
        if math.isnan(if_pp):
            return "nan", "nan"
        return if_pp, ss_pp

    def ss_pp_info(self) -> PerformanceAttributes:
        """
        获取ss pp
        :return: ss pp
        """
        beatmap = Beatmap(path=str(self.osu_file_path))
        mods = [item.acronym for item in self.score.mods]
        if self.score.ruleset_id in {0, 4, 8}:
            mode = GameMode.Osu
        elif self.score.ruleset_id in {1, 5}:
            mode = GameMode.Taiko
        elif self.score.ruleset_id in {2, 6}:
            mode = GameMode.Catch
        else:
            mode = GameMode.Mania
        beatmap.convert(mode, mods=mods)
        c = Performance(
            accuracy=100,
            mods=mods,
        )
        return c.calculate(beatmap)


def get_ss_pp_info(osu_file_path: Path, ruleset_id: int, mods: int) -> PerformanceAttributes:
    """
    获取ss pp
    :param osu_file_path:
    :param ruleset_id:
    :param mods:
    :return:
    """
    beatmap = Beatmap(path=str(osu_file_path))
    if ruleset_id in {0, 4, 8}:
        mode = GameMode.Osu
    elif ruleset_id in {1, 5}:
        mode = GameMode.Taiko
    elif ruleset_id in {2, 6}:
        mode = GameMode.Catch
    else:
        mode = GameMode.Mania
    beatmap.convert(mode, mods=mods)
    c = Performance(
        accuracy=100,
        mods=mods,
    )
    return c.calculate(beatmap)


def find_optimal_new_pp(current_pp_list: list[float], desired_pp_increase: float) -> tuple[float, int]:
    """
    Find the optimal new PP to achieve a desired PP increase given a list of current PP values.

    :param current_pp_list: List of current PP values (list of floats)
    :param desired_pp_increase: Desired increase in total PP (float)
    :return: Tuple of the optimal new PP and the position at which it will be placed
    """

    def calculate_total_pp(pp_list: list[float]) -> float:
        """
        计算 osu! 的总 PP。

        参数:
        pp_list (list[float]): 一个包含每个分数 PP 的列表。

        返回:
        float: 总 PP 值。
        """
        weights = np.array([0.95 ** i for i in range(len(pp_list))], dtype=float)
        total_performance_point = np.sum(np.array(pp_list, dtype=float) * weights)
        return float(total_performance_point)

    if len(current_pp_list) < 100:
        current_pp_list.append(desired_pp_increase)
        current_pp_list.sort(reverse=True)
        return desired_pp_increase, current_pp_list.index(desired_pp_increase) + 1

    total_pp = calculate_total_pp(current_pp_list)
    current_pp_list.sort(reverse=True)
    bp_100 = current_pp_list[99]

    # 使用二分查找来寻找最优的新 PP 值
    low, high = bp_100, bp_100 + desired_pp_increase + 100
    optimal_new_pp = high

    while low <= high:
        mid = (low + high) / 2
        new_pp_list = current_pp_list[:]
        new_pp_list.append(mid)
        new_pp_list.sort(reverse=True)
        new_pp_list.pop()
        new_total_pp = calculate_total_pp(new_pp_list)

        if new_total_pp - total_pp >= desired_pp_increase:
            optimal_new_pp = mid
            high = mid - 0.01
        else:
            low = mid + 0.01

    # 计算 optimal_new_pp 在新排序列表中的位置
    new_pp_list = current_pp_list[:]
    new_pp_list.append(optimal_new_pp)
    new_pp_list.sort(reverse=True)
    position = new_pp_list.index(optimal_new_pp) + 1

    return optimal_new_pp, position

