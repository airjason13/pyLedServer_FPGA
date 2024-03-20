import enum


class PlayStatus(enum.IntEnum):
    Initial = -1
    Stop = 0
    Playing = 1
    Pausing = 2


class PlayType(enum.IntEnum):
    Play_None = 0
    Play_Single = 1
    Play_Playlist = 2
    Play_Hdmi_in = 3
    Play_Cms = 4


class RepeatOption(enum.IntEnum):
    Repeat_None = 0
    Repeat_One = 1
    Repeat_All = 2
    Repeat_Random = 3
    Repeat_Option_Max = 3
