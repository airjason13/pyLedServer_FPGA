import hashlib
import os
import threading

import ffmpy
from global_def import log
from media_configs.media_path_configs import MediaFileFolder, ThumbnailFileFolder
from media_configs.thumbnail_configs import still_image_loop_cnt, preview_period, preview_start_time


def gen_webp_from_video(file_folder, video):
    # use hashlib md5 to generate preview file name
    error_count = 0
    error_count_threshold = 3
    video_name = video.split(".")[0]
    video_extension = video.split(".")[1]
    # log.debug("video_extension = %s", video_extension)
    preview_file_name = hashlib.md5(video_name.encode('utf-8')).hexdigest()

    # thumbnail_path = internal_media_folder + ThumbnailFileFolder + video.replace(".mp4", ".webp")
    thumbnail_path = os.path.expanduser("~" + MediaFileFolder) + ThumbnailFileFolder + preview_file_name + ".webp"
    video_path = file_folder + "/" + video
    # log.debug("video_path = %s", video_path)
    # log.debug("thumbnail_path = %s", thumbnail_path)
    thunbnail_folder_path = os.path.expanduser("~" + MediaFileFolder) + ThumbnailFileFolder
    if not os.path.exists(thunbnail_folder_path):
        os.makedirs(thunbnail_folder_path)
    while True:
        try:
            if os.path.isfile(thumbnail_path) is False:
                global_opts = '-hide_banner -loglevel error'
                if video_extension in ["jpeg", "jpg", "png"]:
                    # log.debug("still image")
                    ff = ffmpy.FFmpeg(
                        global_options=global_opts,
                        inputs={video_path: ['-loop', str(still_image_loop_cnt), '-t', str(preview_period)]},
                        outputs={thumbnail_path: ['-vf', 'scale=320:240']}
                    )
                else:
                    ff = ffmpy.FFmpeg(
                        global_options=global_opts,
                        inputs={video_path: ['-ss', str(preview_start_time), '-t', str(preview_period)]},
                        outputs={thumbnail_path: ['-vf', 'scale=320:240']}
                    )
                # log.debug("%s", ff.cmd)
                ff.run()
        except Exception as e:
            log.debug("Excception %s", e)
            os.remove(thumbnail_path)
            error_count += 1
            if error_count > error_count_threshold:
                log.debug("source file : %s might be fault", video_path)
                break
            continue
        break
    # log.debug("%s generated good", thumbnail_path)
    return thumbnail_path


def gen_webp_from_video_threading(file_folder, video):
    threads = [threading.Thread(target=gen_webp_from_video, args=(file_folder, video,))]
    threads[0].start()