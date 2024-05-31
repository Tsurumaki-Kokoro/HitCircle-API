import math
import numpy as np
from pathlib import Path
from typing import List

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
        mods = self.score.mods.value
        if self.score.mode_int == 0:
            mode = GameMode.Osu
        elif self.score.mode_int == 1:
            mode = GameMode.Taiko
        elif self.score.mode_int == 2:
            mode = GameMode.Catch
        else:
            mode = GameMode.Mania
        beatmap.convert(mode)
        if self.score.mode_int == 2:
            c = Performance(
                accuracy=self.score.accuracy * 100,
                n_katu=self.score.statistics.count_katu,
                combo=self.score.max_combo,
                misses=self.score.statistics.count_miss,
                n100=self.score.statistics.count_100,
                n300=self.score.statistics.count_300,
                mods=mods,
            )

        else:
            c = Performance(
                accuracy=self.score.accuracy * 100,
                n_katu=self.score.statistics.count_katu if self.score.statistics.count_katu else 0,
                n_geki=self.score.statistics.count_geki if self.score.statistics.count_geki else 0,
                combo=self.score.max_combo,
                misses=self.score.statistics.count_miss if self.score.statistics.count_miss else 0,
                n50=self.score.statistics.count_50 if self.score.statistics.count_50 else 0,
                n100=self.score.statistics.count_100 if self.score.statistics.count_100 else 0,
                n300=self.score.statistics.count_300 if self.score.statistics.count_300 else 0,
                mods=mods,
            )

        return c.calculate(beatmap)

    def if_pp_ss_pp_info(self) -> tuple[float, float] | tuple[str, str]:
        """
        获取 if fc pp 和 ss pp
        :return: if pp 和 ss pp
        """
        beatmap = Beatmap(path=str(self.osu_file_path))
        mods = self.score.mods.value
        if self.score.mode_int == 0:
            mode = GameMode.Osu
        elif self.score.mode_int == 1:
            mode = GameMode.Taiko
        elif self.score.mode_int == 2:
            mode = GameMode.Catch
        else:
            mode = GameMode.Mania
        beatmap.convert(mode)
        c = Performance(
            accuracy=self.score.accuracy * 100,
            n_katu=self.score.statistics.count_katu if self.score.statistics.count_katu else 0,
            n_geki=self.score.statistics.count_geki if self.score.statistics.count_geki else 0,
            n50=self.score.statistics.count_50 if self.score.statistics.count_50 else 0,
            n100=self.score.statistics.count_100 if self.score.statistics.count_100 else 0,
            n300=self.score.statistics.count_300 + self.score.statistics.count_miss,
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
        mods = self.score.mods.value
        if self.score.mode_int == 0:
            mode = GameMode.Osu
        elif self.score.mode_int == 1:
            mode = GameMode.Taiko
        elif self.score.mode_int == 2:
            mode = GameMode.Catch
        else:
            mode = GameMode.Mania
        beatmap.convert(mode)
        c = Performance(
            accuracy=100,
            mods=mods,
        )
        return c.calculate(beatmap)


def get_ss_pp_info(osu_file_path: Path, mode: int, mods: int) -> PerformanceAttributes:
    """
    获取ss pp
    :param osu_file_path:
    :param mode:
    :param mods:
    :return:
    """
    beatmap = Beatmap(path=str(osu_file_path))
    if mode == 0:
        mode = GameMode.Osu
    elif mode == 1:
        mode = GameMode.Taiko
    elif mode == 2:
        mode = GameMode.Catch
    else:
        mode = GameMode.Mania
    beatmap.convert(mode)
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
        total_pp = np.sum(np.array(pp_list, dtype=float) * weights)
        return total_pp

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

