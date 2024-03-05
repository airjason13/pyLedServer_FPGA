import glob
import os.path
import platform
import subprocess
import sys
import time
import psutil
import pyudev
from global_def import log, SU_PWD, root_dir


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
        if platform.machine().split('_')[0] in file_format:
            return True
    except Exception as e:
        log.debug(e)
        return False

    return False


def run_cmd_with_su(command, sudo_password=SU_PWD):
    command_with_su = 'sudo -S ' + command
    p1 = subprocess.run('echo ' + sudo_password, stdin=None, stdout=subprocess.PIPE, shell=True, encoding='UTF-8')
    ret = subprocess.run(command_with_su, input=p1.stdout, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, encoding='UTF-8')
    # ret = subprocess.run(command_with_su, input=p1.stdout, shell=True, encoding='UTF-8')
    if ret.returncode == 0:
        log.debug('success')
    else:
        log.error('error')
    return ret.stdout


def set_os_environ():
    ext_binaries_path = "{}/ext_binaries".format(root_dir)
    if ext_binaries_path not in os.environ['PATH']:
        os.environ['PATH'] += os.pathsep + ext_binaries_path


def check_and_rebuild_binaries():
    log.debug("check_and_rebuild_binaries")
    # check linux_ipc_sem file format is match or not
    linux_ipc_sem_lib_uri = "{}/ext_binaries/liblinux_ipc_sem_pyapi.so".format(root_dir)
    show_ffmpeg_shared_memory_exec_uri = "{}/ext_binaries/show_ffmpeg_shared_memory".format(root_dir)
    if not determine_file_match_platform(linux_ipc_sem_lib_uri):
        log.debug("rebuild linux_ipc_sem")
        sub_path = '/ext_binaries/linux_ipc_sem/'
        rebuild_cmd = (
            'cd {}{} && . {}{}build_so.sh'.format(root_dir, sub_path, root_dir, sub_path))
        log.debug("check rebuild_cmd : %s", rebuild_cmd)
        log.debug("rebuild_cmd : %s", rebuild_cmd)
        subprocess.Popen(rebuild_cmd, shell=True)
        if os.path.exists("/usr/lib/liblinux_ipc_sem_pyapi.so"):
            rm_ld_link_cmd = 'echo {} | sudo -S rm /usr/lib/liblinux_ipc_sem_pyapi.so'.format(SU_PWD)
            log.debug("rm_ld_link_cmd : %s", rm_ld_link_cmd)
            subprocess.Popen(rm_ld_link_cmd, shell=True)

        mk_soft_link_cmd = \
            f'echo {SU_PWD} | sudo -S ln -s {root_dir}{sub_path}liblinux_ipc_sem_pyapi.so /usr/lib/liblinux_ipc_sem_pyapi.so'
        log.debug("mk_soft_link_cmd : %s", mk_soft_link_cmd)
        subprocess.Popen(mk_soft_link_cmd, shell=True)
        time.sleep(1)
        os.sync()

    if not determine_file_match_platform(show_ffmpeg_shared_memory_exec_uri):
        log.debug("rebuild show_ffmpeg_shared_memory_exec_uri")
        sub_path = '/ext_binaries/ffmpeg_shared_memory/'

        rebuild_cmd = (
            'cd {}{} && {}{}build_show_ffmpeg_shared_memory.sh {}'.format(root_dir, sub_path, root_dir, sub_path, SU_PWD))
        log.debug("rebuild_cmd : %s", rebuild_cmd)
        subprocess.Popen(rebuild_cmd, shell=True)
        time.sleep(1)
        os.sync()