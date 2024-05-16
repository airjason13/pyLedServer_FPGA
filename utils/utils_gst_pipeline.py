import platform
from global_def import log


def get_gst_cmd_for_media(video_uri: str, **kwargs):
    active_width = kwargs.get("active_width")
    active_height = kwargs.get("active_height")
    output_width = kwargs.get("output_width", 1280)
    output_height = kwargs.get("output_height", 720)
    target_fps = kwargs.get("target_fps", "24/1")
    video_sink = kwargs.get("video_sink")
    c_width = kwargs.get("c_width")
    c_height = kwargs.get("c_height")
    c_pos_x = kwargs.get("c_pos_x")
    c_pos_y = kwargs.get("c_pos_y")

    pipeline_description = None

    if "/dev/video" in video_uri:
        if "pi5" in platform.node():
            pipeline_description = (
                f"v4l2src device={video_uri} ! "
                f"video/x-raw, width={active_width}, height={active_height}, format=UYVY ! "
                "videoconvert ! "
                "videoscale ! "
                f"video/x-raw, width={output_width}, height={output_height}, "
                f"format=RGB, framerate={target_fps} ! "
                "tee name=t "
            )
        elif "x86_64" in platform.machine():
            '''
            pipeline_description = (
                f"v4l2src device={video_uri} ! "
                f"video/x-raw, width={active_width}, height={active_height}, format=YUY2 ! "
                "videoconvert ! "
                "videoscale ! "
                f"video/x-raw, width={output_width}, height={output_height}, "
                f"format=RGB, framerate=30/1 ! "
                "tee name=t "
            )
            '''
            pipeline_description = (
                f"v4l2src device={video_uri} ! "
                f"image/jpeg, width={active_width}, height={active_height}, framerate=30/1 ! "
                "jpegdec ! "
                "videoconvert ! "
                "videoscale ! "
                f"video/x-raw, width={output_width}, height={output_height}, "
                f"format=RGB, framerate=30/1 ! "
                "tee name=t "
            )

        if video_sink:
            pipeline_description += (
                "t. ! queue ! videoconvert ! autovideosink "
            )

        pipeline_description += (
            "t. ! queue ! videoconvert ! appsink name=sink emit-signals=True "
            "max-buffers=1 drop=True sync=False"
        )

    log.debug("gst pipeline description: %s", pipeline_description)
    return pipeline_description

