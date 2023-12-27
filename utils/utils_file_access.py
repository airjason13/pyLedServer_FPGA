import glob
import os.path

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
    # print("type(file_list) = %s", type(file_list))
    return file_list

