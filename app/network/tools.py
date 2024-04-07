def int_to_osu_mode(mode: int) -> str:
    if mode == 0:
        return "osu"
    elif mode == 1:
        return "taiko"
    elif mode == 2:
        return "fruits"
    elif mode == 3:
        return "mania"
    else:
        return "osu"
