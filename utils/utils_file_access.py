import glob
import os.path
import platform
import subprocess
import sys

import psutil
import pyudev
from global_def import log


def get_mount_points(devices=None):
    context = pyudev.Context()

    mount_points = []
    # 分割磁區的pen drive
    removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if
                 device.attributes.asstring('removable') == "1"]
    for device in removable:
        partitions = [device.device_node for device in
                      context.list_devices(subsystem='block', DEVTYPE='partition', parent=device)]

        for p in psutil.disk_partitions():
            if p.device in partitions:
                mount_points.append(p.mountpoint)

    # 未分割磁區的pen drive
    for device in removable:
        partitions = [device.device_node for device in
                      context.list_devices(subsystem='block', DEVTYPE='disk', parent=device)]

        for p in psutil.disk_partitions():
            if p.device in partitions:
                mount_points.append(p.mountpoint)
    return mount_points


def get_playlist_file_list(dir, with_path=False):
    log.debug("dir : %s", dir)
    if os.path.isdir(dir) is False:
        cmd = 'mkdir -p ' + dir
        os.system(cmd)
    file_list = glob.glob(dir + "/*.playlist")
    return file_list


def get_led_config_from_file_uri(file_name, *args):
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    with open(os.path.join(led_config_dir, file_name), "r") as f:
        lines = f.readlines()
    f.close()

    ret_val = [''] * len(args)
    for i in range(len(args)):
        log.debug("arg : %s", args[i])
        for line in lines:
            if args[i] in line:
                ret_val[i] = line.split("=")[1].strip("\n")

    return ret_val


def get_int_led_config_from_file_uri(file_name, *args):
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    with open(os.path.join(led_config_dir, file_name), "r") as f:
        lines = f.readlines()
    f.close()

    ret_val = [''] * len(args)
    for i in range(len(args)):
        log.debug("arg : %s", args[i])
        for line in lines:
            if args[i] in line:
                ret_val[i] = int(line.split("=")[1].strip("\n"))

    return ret_val


def determine_file_match_platform(file_uri) -> bool:
    try:
        cmd = 'file {}'.format(file_uri)
        log.debug("cmd = %s", cmd)
        file_format = os.popen(cmd).read()
        log.debug("platform.machine() : %s", platform.machine())
        log.debug("file_format : %s", file_format)
        ''' Need to check later'''
        if platform.machine() in file_format:
            return True
    except Exception as e:
        log.debug(e)
        return False

    return False
