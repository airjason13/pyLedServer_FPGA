from global_def import log

def get_gstreamer_cmd_for_media(video_uri: str, **kwargs):
    width = kwargs.get("width", 1280)
    height = kwargs.get("height", 720)
    target_fps = kwargs.get("target_fps", "24/1")
    c_width = kwargs.get("c_width")
    c_height = kwargs.get("c_height")
    c_pos_x = kwargs.get("c_pos_x", 0)
    c_pos_y = kwargs.get("c_pos_y", 0)
    i_width = kwargs.get("i_width", width)
    i_height = kwargs.get("i_height", height)
    audio_sink = kwargs.get("audio_sink", "autoaudiosink")
    audio_on = kwargs.get("audio_on", True)

    log.debug(f"i_width: {i_width}, i_height: {i_height}, c_pos_x: {c_pos_x}, c_pos_y: {c_pos_y}, c_width: {c_width}, c_height: {c_height}")

    # Define cropping and scaling with RGB format
    if c_width and c_height:
        crop_filter = f"videocrop left={c_pos_x} right={max(i_width - (c_pos_x + c_width), 0)} top={c_pos_y} bottom={max(i_height - (c_pos_y + c_height), 0)}"
    else:
        crop_filter = ""

    scale_filter = f"videoscale ! video/x-raw,format=RGB,width={width},height={height}"
    filter_chain = ' ! '.join(filter(None, [crop_filter, scale_filter]))

    # Construct the pipeline based on video URI type
    if "/dev/video" in video_uri:
        pipeline_str = (
            f"v4l2src device={video_uri} ! videoconvert ! {filter_chain} "
            f"! videorate ! video/x-raw,framerate={target_fps} ! appsink name=appsink_sink"
        )
        if audio_on:
            pipeline_str += f" alsasrc device={audio_sink} ! audioconvert ! audioresample ! autoaudiosink"

    elif video_uri.endswith(".mp4"):
        pipeline_str = (
            f"filesrc location={video_uri} ! decodebin name=demux "
            f"demux. ! queue ! videoconvert ! {filter_chain} ! videorate ! video/x-raw,framerate={target_fps} ! appsink name=appsink_sink"
        )
        if audio_on:
            pipeline_str += f" demux. ! queue ! audioconvert ! audioresample ! {audio_sink}"

    elif video_uri.endswith((".jpeg", ".jpg", ".png")):
        pipeline_str = (
            f"filesrc location={video_uri} ! "
            f"{'jpegdec' if video_uri.endswith(('.jpeg', '.jpg')) else 'pngdec'} ! "
            "imagefreeze ! videoscale ! "
            f"video/x-raw,width={width},height={height},framerate={target_fps} ! "
            "videorate ! videoconvert ! video/x-raw,format=RGB ! "
            "appsink name=appsink_sink"
        )
    else:
        pipeline_str = (
            f"ximagesrc display-name={video_uri} use-damage=0 ! "
            f"video/x-raw,format=RGB,framerate={target_fps},width={width},height={height} "
            f"! videoconvert ! {filter_chain} ! appsink name=appsink_sink"
        )

    return pipeline_str
