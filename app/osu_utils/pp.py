import math
from pathlib import Path

from ossapi import Score
from rosu_pp_py import PerformanceAttributes, Beatmap, Calculator


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
        if self.score.mode_int == 2:
            c = Calculator(
                acc=self.score.accuracy * 100,
                n_katu=self.score.statistics.count_katu,
                combo=self.score.max_combo,
                n_misses=self.score.statistics.count_miss,
                n100=self.score.statistics.count_100,
                n300=self.score.statistics.count_300,
                mods=mods,
                mode=self.score.mode_int
            )

        else:
            c = Calculator(
                acc=self.score.accuracy * 100,
                n_katu=self.score.statistics.count_katu,
                n_geki=self.score.statistics.count_geki,
                combo=self.score.max_combo,
                n_misses=self.score.statistics.count_miss,
                n50=self.score.statistics.count_50,
                n100=self.score.statistics.count_100,
                n300=self.score.statistics.count_300,
                mods=mods,
                mode=self.score.mode_int
            )

        return c.performance(beatmap)

    def if_pp_ss_pp_info(self) -> tuple[float, float] | tuple[str, str]:
        """
        获取 if fc pp 和 ss pp
        :return: if pp 和 ss pp
        """
        beatmap = Beatmap(path=str(self.osu_file_path))
        mods = self.score.mods.value
        c = Calculator(
            acc=self.score.accuracy * 100,
            n_katu=self.score.statistics.count_katu,
            n_geki=self.score.statistics.count_geki,
            n50=self.score.statistics.count_50,
            n100=self.score.statistics.count_100,
            n300=self.score.statistics.count_300 + self.score.statistics.count_miss,
            mods=mods,
            mode=self.score.mode_int,
        )
        if_pp = c.performance(beatmap).pp
        c = Calculator(acc=100, mods=mods, mode=self.score.mode_int)
        ss_pp = c.performance(beatmap).pp
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
        c = Calculator(
            acc=100,
            mods=mods,
            mode=self.score.mode_int
        )
        return c.performance(beatmap)


def get_ss_pp_info(osu_file_path: Path, mode: int, mods: int) -> PerformanceAttributes:
    """
    获取ss pp
    :param osu_file_path:
    :param mode:
    :param mods:
    :return:
    """
    beatmap = Beatmap(path=str(osu_file_path))
    c = Calculator(
        acc=100,
        mods=mods,
        mode=mode
    )
    return c.performance(beatmap)
