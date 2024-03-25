import platform

import ffmpy
from global_def import log


def get_ffmpeg_cmd_with_playing_media_file_(video_uri: str, **kwargs):
    log.debug("video_uri : %s", video_uri)
    log.debug("%s", kwargs)
    log.debug("%d", kwargs.get("width"))
    log.debug("%d", kwargs.get("height"))
    ff = None
    width = kwargs.get("width", 1280)
    height = kwargs.get("height", 720)
    target_fps = kwargs.get("target_fps", "24/1")
    image_period = kwargs.get("image_period")
    global_opts = '-hide_banner -loglevel error -hwaccel auto'
    scale_param = 'scale=' + str(width) + ':' + str(height)
    filter_params = scale_param
    pipe_sink = '-'
    # unix_socket = 'unix:///home/root/ffmpeg_unix_socket/ffmpeg_unix_socket'
    if platform.machine() in ('arm', 'arm64', 'aarch64'):
        audio_sink = 'hw:1,0'
    else:
        audio_sink = 'hw:0,0'

    if "/dev/video" in video_uri:
        ff = ffmpy.FFmpeg(
            inputs={video_uri: None},
            outputs={
                pipe_sink: ["-loglevel", "error", "-vf", scale_param, "-r", target_fps, "-pix_fmt", "rgb24", "-f", "rawvideo"],
                # audio_sink: ["-f", "alsa"]
            }
        )
    elif video_uri.endswith("mp4"):
        ff = ffmpy.FFmpeg(
            global_options=global_opts,
            inputs={
                video_uri: ["-re"]
            },
            outputs={
                pipe_sink: ["-filter_complex", filter_params, "-r", target_fps, "-pix_fmt", "rgb24", "-f", "rawvideo"],
                # unix_socket: ["-f", "rawvideo"],
                audio_sink: ["-f", "alsa"]
            },
        )
    elif video_uri.endswith("jpeg") or video_uri.endswith("jpg") or video_uri.endswith("png"):
        log.debug("jpg to mp4")
        ff = ffmpy.FFmpeg(
            global_options=global_opts,
            inputs={
                video_uri: ["-loop", str(1), "-t", str(image_period), "-re"]
                # video_uri: []
            },
            outputs={
                pipe_sink: ["-filter_complex", filter_params, "-r", target_fps,  "-pix_fmt", "rgb24", "-f", "rawvideo"]
                # pipe_sink: []
            },
        )

    log.debug("ff.cmd : %s", ff.cmd)
    ff.cmd += " -y"
    return ff.cmd




