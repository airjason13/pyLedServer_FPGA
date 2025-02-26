import os
import subprocess
import time
import sys
from global_def import *
from ctypes import *

import psutil
import ctypes
import numpy as np

class LinuxDrmPyapi:
    def __init__(self):
        super().__init__()

        self.pos_x = None
        self.pos_y = None
        self.height = None
        self.width = None
        self.px_size = None
        self.fps = None
        self.fb_image_data = None
        self.library = None
        self.initialize_library()

    def initialize_library(self):
        prj_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
        lib_path_local = f"{prj_dir}/ext_binaries/linux_libdrm.so"
        lib_path_usr = "/usr/lib/linux_libdrm.so"

        if not os.path.exists(lib_path_local):
            log.debug("Rebuilding linux_libdrm.so")
            sub_path = "/ext_binaries/linux_drm/"
            rebuild_cmd = f"cd {prj_dir}{sub_path} && . {prj_dir}{sub_path}build_so.sh"
            log.debug("Rebuild command: %s", rebuild_cmd)
            ps_tmp = subprocess.Popen(rebuild_cmd, shell=True)
            ps_tmp.wait()

            if os.path.exists(lib_path_usr):
                rm_ld_link_cmd = f'echo {SU_PWD} | sudo -S rm {lib_path_usr}'
                log.debug("Remove old symbolic link: %s", rm_ld_link_cmd)
                ps_tmp = subprocess.Popen(rm_ld_link_cmd, shell=True)
                ps_tmp.wait()

            mk_soft_link_cmd = f'echo {SU_PWD} | sudo -S ln -s {lib_path_local} {lib_path_usr}'
            log.debug("Create symbolic link: %s", mk_soft_link_cmd)
            ps_tmp = subprocess.Popen(mk_soft_link_cmd, shell=True)
            ps_tmp.wait()
            time.sleep(1)
            os.sync()

        try:
            if os.path.exists(lib_path_usr):
                self.library = ctypes.CDLL(lib_path_usr)
                log.debug("Loaded library from %s", lib_path_usr)
            elif os.path.exists(lib_path_local):
                self.library = ctypes.CDLL(lib_path_local)
                log.debug("Loaded library from %s", lib_path_local)
            else:
                log.debug("linux_libdrm.so not found.")

            self.set_function_prototypes()
        except OSError as e:
            log.debug("Failed to load linux_libdrm.so: %s", str(e))
            raise

    def set_function_prototypes(self):
        try:
            # drm_initialize
            self.library.drm_initialize.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self.library.drm_initialize.restype = ctypes.c_int

            # drm_capture_format
            self.library.drm_capture_format.argtypes = [
                ctypes.c_int,  # width
                ctypes.c_int,  # height
                ctypes.c_int  # px_size
            ]
            self.library.drm_capture_format.restype = None

            # drm_capture_frame
            self.library.drm_capture_frame.argtypes = [
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.c_int,  # x_offset
                ctypes.c_int,  # y_offset
                ctypes.c_int,  # capture_width
                ctypes.c_int  # capture_height
            ]
            self.library.drm_capture_frame.restype = ctypes.c_int

            # drm_set_color_space
            self.library.drm_set_color_space.argtypes = [ctypes.c_char_p]
            self.library.drm_set_color_space.restype = None

            # drm_cleanup
            self.library.drm_cleanup.restype = None
            self.library.drm_cleanup.argtypes = []

            log.debug("Function prototypes set successfully.")
        except AttributeError as e:
            log.debug("Error setting function prototypes: %s", str(e))
            raise

    def open(self):

        try:
            device_path = b"/dev/dri/card1"
            result = self.library.drm_initialize(device_path, -1)
            if result != 0:
                log.debug("Failed to initialize DRM on device: %s", device_path.decode())
                return False
            return True
        except Exception as e:
            log.debug("Error during DRM( initialization: %s", str(e))
            return False

    def configure_fb(self, width, height, px_size , pos_x, pos_y):
        self.px_size = px_size
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height

        log.debug(f"Configuring frame buffer: width={width}, height={height}, px_size={px_size},"
                  f" pos_x={pos_x}, pos_y={pos_y}")
        self.fb_image_data = np.zeros((height, width, px_size), dtype=np.uint8)
        self.library.drm_capture_format(width, height, px_size)

    def color_space(self,color_space):
        valid_spaces = ["ABGR", "RGB"]
        if color_space not in valid_spaces:
            log.debug(f"Invalid color space: {color_space}. Valid options: {valid_spaces}")
            return

        self.library.drm_set_color_space(color_space.encode('utf-8'))

    def capture_frame(self):

        if self.fb_image_data is None:
            log.debug("Frame buffer is not initialized.")
            return False

        result = self.library.drm_capture_frame(
            self.fb_image_data.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),
            self.pos_x, self.pos_y, self.width, self.height
        )
        if result != 0:
            log.debug("Failed to capture frame")
            return False

        return True

    def release_drm(self):
        self.library.drm_cleanup()
    
