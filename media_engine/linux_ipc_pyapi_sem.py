import os
import subprocess
import time
import sys
from global_def import *
from ctypes import *


class LinuxIpcSemaphorePyapi:
    if not os.path.exists("{}/ext_binaries/liblinux_ipc_sem_pyapi.so".format(root_dir)):
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

    library = cdll.LoadLibrary("{}/ext_binaries/liblinux_ipc_sem_pyapi.so".format(root_dir))
    sem_flag = 0

    def sem_open(self, sem_name, oflag, mode, value):

        self.library.py_sem_open.argtypes = [c_char_p, c_int, c_uint, c_uint]
        self.library.py_sem_open.restype = c_void_p

        name = create_string_buffer(sem_name.encode('utf-8'))
        self.sem_flag = self.library.py_sem_open(name, c_int(oflag), c_uint(mode), c_uint(value))
        return self.sem_flag

    def sem_close(self, sem_flag):
        self.library.py_sem_close.argtypes = [c_void_p, ]
        self.library.py_sem_close.restype = c_int

        flag = self.library.py_sem_close(c_void_p(sem_flag))

        return flag

    def sem_unlink(self, sem_name):
        self.library.py_sem_unlink.argtypes = [c_char_p, ]
        self.library.py_sem_unlink.restype = c_int

        name = create_string_buffer(sem_name.encode('utf-8'))
        flag = self.library.py_sem_unlink(name)
        return flag

    def sem_wait(self, sem_flag):
        self.library.py_sem_wait.argtypes = [c_void_p, ]
        self.library.py_sem_wait.restype = c_int

        flag = self.library.py_sem_wait(c_void_p(sem_flag))
        return flag

    def sme_timedwait(self, sem_flag, time_secs, time_nsecs):
        self.library.py_sem_timedwait.argtypes = [c_void_p, c_int64, c_int64]
        self.library.py_sem_timedwait.restype = c_int

        flag = self.library.py_sem_timedwait(c_void_p(sem_flag), c_int64(time_secs), c_int64(time_nsecs))
        return flag

    def sem_trywait(self, sem_flag):
        self.library.py_sem_trywait.argtypes = [c_void_p, ]
        self.library.py_sem_trywait.restype = c_int

        flag = self.library.py_sem_trywait(c_void_p(sem_flag))
        return flag

    def sem_post(self, sem_flag):
        self.library.py_sem_post.argtypes = [c_void_p, ]
        self.library.py_sem_post.restype = c_int

        flag = self.library.py_sem_post(c_void_p(sem_flag))

        return flag

    def sem_getvalue(self, sem_flag):
        self.library.py_sem_getvalue.argtypes = [c_void_p]
        self.library.py_sem_getvalue.restype = c_int

        ret_val = self.library.py_sem_getvalue(c_void_p(sem_flag))
        if ret_val < 0:
            print("failed to get sem val")
        return ret_val
