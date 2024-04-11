import math
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
