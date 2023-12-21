import platform
import subprocess
from global_def import log


def get_throttled_to_log():
    if platform.machine() in ('arm', 'arm64', 'aarch64'):
        try:
            get_throttled = subprocess.Popen("vcgencmd get_throttled", shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = get_throttled.communicate()
            # log.debug("get_throttled : %s", stdout.decode())
            if stdout.decode() != "throttled=0x0\n":
                log.debug("A error get_throttled : %s", stdout.decode())
            get_throttled.terminate()
        except Exception as e:
            log.debug("error!")
        finally:
            pass
    else:
        pass
