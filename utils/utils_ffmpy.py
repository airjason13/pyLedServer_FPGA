import ffmpy
from global_def import log


def get_ffmpeg_cmd_with_playing_media_file_(video_uri, **kwargs):
    log.debug("%s", kwargs)
    log.debug("%d", kwargs.get("width"))
