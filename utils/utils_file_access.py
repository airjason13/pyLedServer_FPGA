import glob
import json
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


def get_file_list_in_playlist(playlist_uri):
    file_list = []
    if os.path.isfile(playlist_uri):
        with open(playlist_uri, "r") as f:
            lines = f.readlines()
        f.close()
        for line in lines:
            line = line.strip("\n")
            file_list.append(line)
        return file_list
    return None


def get_fpga_config_file_list(dir, with_path=False):
    log.debug("dir : %s", dir)
    if os.path.isdir(dir) is False:
        cmd = 'mkdir -p ' + dir
        os.system(cmd)
    file_list = glob.glob(dir + "/*.json")
    return file_list


def get_fpga_ota_file_list(dir, with_path=False):
    log.debug("dir : %s", dir)
    if os.path.isdir(dir) is False:
        cmd = 'mkdir -p ' + dir
        os.system(cmd)
    file_list = glob.glob(dir + "/*.bit")
    return file_list


def get_led_config_from_file_uri(file_name, *args) -> list[str]:
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


def get_int_led_config_from_file_uri(file_name, *args) -> int:
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    with open(os.path.join(led_config_dir, file_name), "r") as f:
        lines = f.readlines()
    f.close()

    ret_val = [''] * len(args)
    for i in range(len(args)):
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
        ps_tmp = subprocess.Popen(rebuild_cmd, shell=True)
        ps_tmp.wait()
        if os.path.exists("/usr/lib/liblinux_ipc_sem_pyapi.so"):
            rm_ld_link_cmd = 'echo {} | sudo -S rm /usr/lib/liblinux_ipc_sem_pyapi.so'.format(SU_PWD)
            log.debug("rm_ld_link_cmd : %s", rm_ld_link_cmd)
            ps_tmp = subprocess.Popen(rm_ld_link_cmd, shell=True)
            ps_tmp.wait()

        mk_soft_link_cmd = \
            f'echo {SU_PWD} | sudo -S ln -s {root_dir}{sub_path}liblinux_ipc_sem_pyapi.so /usr/lib/liblinux_ipc_sem_pyapi.so'
        log.debug("mk_soft_link_cmd : %s", mk_soft_link_cmd)
        ps_tmp = subprocess.Popen(mk_soft_link_cmd, shell=True)
        ps_tmp.wait()
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


def load_fpga_json_file(file_uri: str) -> dict:
    log.debug("load_fpga_json_file")
    with open(file_uri, "r") as jsonFile:
        python_dict = json.load(fp=jsonFile)
        # log.debug("python_dict : %s", python_dict)
        # print("type(python_dict) : ", type(python_dict))
        # log.debug("python_dict : %s", python_dict)

    return python_dict


def set_sleep_params(start_time, end_time):
    str_sleep_start_time = "sleep_start_time=" + start_time + "\n"
    str_sleep_end_time = "sleep_end_time=" + end_time + "\n"
    content_lines = [
        str_sleep_start_time,
        str_sleep_end_time,
    ]
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    file_uri = os.path.join(led_config_dir, "sleep_time_config")
    config_file = open(file_uri, 'w')
    config_file.writelines(content_lines)
    config_file.close()
    os.system('sync')


def init_sleep_time_params():
    content_lines = [
        "sleep_start_time=00:30\n",
        "sleep_end_time=04:30\n",
    ]
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    file_uri = os.path.join(led_config_dir, "sleep_time_config")
    config_file = open(file_uri, 'w')
    config_file.writelines(content_lines)
    config_file.close()
    os.system('sync')


def get_sleep_time_from_file():
    s_start_time = ""
    s_end_time = ""
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    if os.path.isfile(os.path.join(led_config_dir, "sleep_time_config")) is False:
        init_sleep_time_params()

    with open(os.path.join(led_config_dir, "sleep_time_config"), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        if "sleep_start_time" in line:
            s_start_time = line.split("=")[1].strip("\n")
        if "sleep_end_time" in line:
            s_end_time = line.split("=")[1].strip("\n")

    return s_start_time, s_end_time
