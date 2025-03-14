import ctypes
import numpy as np
import subprocess
import time
import platform

drm = ctypes.CDLL('./linux_libdrm.so')
drm.drm_initialize.argtypes = [ctypes.c_char_p,ctypes.c_int]
drm.drm_initialize.restype = ctypes.c_int
arch = platform.machine()

drm.drm_capture_format.argtypes = [
    ctypes.c_int,  # width
    ctypes.c_int,  # height
    ctypes.c_int   # px_size
]
drm.drm_capture_format.restype = None

drm.drm_capture_frame.argtypes = [
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_int,  # x_offset
    ctypes.c_int,  # y_offset
    ctypes.c_int,  # capture_width
    ctypes.c_int,  # capture_height
]
drm.drm_capture_frame.restype = ctypes.c_int

drm.drm_cleanup.restype = None
drm.drm_cleanup.argtypes = []

if drm.drm_initialize(b"/dev/dri/card1",-1) != 0:
    print("Failed to initialize DRM")
    exit(1)

capture_width = 640
capture_height = 480
capture_px_size = 3
buffer = np.zeros((capture_height, capture_width, capture_px_size), dtype=np.uint8)
drm.drm_capture_format(capture_width,capture_height,capture_px_size)
if arch in ["x86_64"]:
    gst_command = (
        "gst-launch-1.0 fdsrc ! videoparse width=640 height=480 format=rgb framerate=25/1 ! videoconvert ! "
        "videoscale ! video/x-raw,width=640,height=480 ! "
        "videoconvert ! videorate ! video/x-raw,framerate=25/1 ! "
        "ximagesink  window-width=640 window-height=480 sync=false "
    );
else:
    gst_command = (
        "gst-launch-1.0 fdsrc ! videoparse width=640 height=480 format=bgra framerate=25/1 ! imxvideoconvert_g2d ! " 
	    "videoscale ! video/x-raw,width=640,height=480 ! "
	    "videoconvert ! videorate ! video/x-raw,framerate=25/1 ! "
        "waylandsink  window-width=640 window-height=480 sync=false "
    );

gstreamer_process = subprocess.Popen(
    gst_command,
    shell=True,
    stdin=subprocess.PIPE,
)

try:
    while True:
        if drm.drm_capture_frame(buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), 100, 100, capture_width, capture_height) != 0:
            print("Failed to capture frame")
            break

        gstreamer_process.stdin.write(buffer.tobytes())
        gstreamer_process.stdin.flush()
        time.sleep(1 / 25)
finally:
    gstreamer_process.stdin.close()
    gstreamer_process.terminate()
    drm.drm_cleanup()

