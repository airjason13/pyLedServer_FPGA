import os
import platform
import subprocess

import ffmpy
from global_def import log


def get_ffmpeg_cmd_for_media(video_uri: str, **kwargs):
    log.debug("video_uri : %s", video_uri)
    log.debug("%s", kwargs)
    log.debug("width %d", kwargs.get("width"))
    log.debug("height %d", kwargs.get("height"))
    log.debug("window_width: %d", kwargs.get("window_width", 0))
    log.debug("window_height: %d", kwargs.get("window_height", 0))
    ff = None
    width = kwargs.get("width", 1280)
    height = kwargs.get("height", 720)

    window_width = kwargs.get("window_width", 640)
    window_height = kwargs.get("window_height", 480)

    target_fps = kwargs.get("target_fps", "24/1")
    c_width = kwargs.get("c_width")
    c_height = kwargs.get("c_height")
    c_pos_x = kwargs.get("c_pos_x")
    c_pos_y = kwargs.get("c_pos_y")
    image_period = kwargs.get("image_period")
    audio_sink = kwargs.get("audio_sink", "hw:1,0")
    audio_on = kwargs.get("audio_on", True)
    global_opts = '-hide_banner -loglevel error -hwaccel auto'
    scale_param = 'scale=' + str(width) + ':' + str(height)
    crop_param = f"crop={c_width}:{c_height}:{c_pos_x}:{c_pos_y}" if c_width and c_height else ""
    filter_params = ','.join(filter(None, [crop_param, scale_param]))
    pipe_sink = '-'

    window_size_params = str(window_width) + "x" + str(window_height)
    # unix_socket = 'unix:///home/root/ffmpeg_unix_socket/ffmpeg_unix_socket'
    if "/dev/video" in video_uri:

        ff = ffmpy.FFmpeg(
            inputs={video_uri: None},
            outputs = {
                pipe_sink: [
                    "-loglevel", "error","-vf", f"fps={target_fps},{filter_params}","-pix_fmt", "rgb24","-f", "rawvideo"],
                # audio_sink: ["-f", "alsa"]
            }
        )
    elif video_uri.endswith("mp4"):
        output_options = {
            pipe_sink: ["-filter_complex", filter_params, "-r", target_fps, "-pix_fmt", "rgb24", "-f", "rawvideo"]
        }
        if audio_on:
            # 檢查影片緣是否帶有音軌
            got_audio = False
            process = subprocess.Popen(['ffprobe', '-hide_banner', video_uri],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            ffprobe_res = process.communicate()
            for byte_res in ffprobe_res:
                if "Audio" in byte_res.decode():
                    got_audio = True

            log.debug("got_audio : %d", got_audio)
            if got_audio is True:
                output_options[audio_sink] = ["-f", "alsa"]

        ff = ffmpy.FFmpeg(
            global_options=global_opts,
            inputs={video_uri: ["-re"]},
            outputs=output_options
        )
    elif video_uri.endswith("jpeg") or video_uri.endswith("jpg") or video_uri.endswith("png"):
        log.debug("jpg to mp4")
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            pass
        else:
            # nvidia cuda does not support jeg decode
            global_opts = '-hide_banner -loglevel error'
        ff = ffmpy.FFmpeg(
            global_options=global_opts,
            inputs={
                video_uri: ["-loop", str(1), "-t", str(image_period), "-re"]
                # video_uri: []
            },
            outputs={
                pipe_sink: ["-filter_complex", filter_params, "-r", target_fps, "-pix_fmt", "rgb24", "-f", "rawvideo"]
                # pipe_sink: []
            },
        )
    else: # elif video_uri.endswith("CMS"):
        ff = ffmpy.FFmpeg(
            inputs={
                video_uri: ["-f", "x11grab", "-video_size", window_size_params]
            },
            outputs={
                pipe_sink: ["-loglevel", "error", "-vf", filter_params, "-r", target_fps, "-pix_fmt", "rgb24", "-f",
                            "rawvideo"],
            }
        )


    log.debug("ff.cmd : %s", ff.cmd)
    ff.cmd += " -y"
    return ff.cmd


def get_media_resolution_from_ffmpeg(file_uri):
    ff = ffmpy.FFmpeg(
        inputs={file_uri: None},
        outputs={'': None}
    )
    return ff.cmd
