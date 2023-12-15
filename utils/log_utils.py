import logging
from logging.handlers import RotatingFileHandler
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

log_level = logging.DEBUG
# log_level = logging.INFO
# log_level = logging.ERROR

import os
import sys
root_dir = os.path.dirname(sys.modules['__main__'].__file__)
log_dir = os.path.join(root_dir, 'log')
print("log_dir = ", log_dir)

os.makedirs(log_dir, exist_ok=True)

def set_logging_level(l):
    global log_level
    log_level = l

def logging_init(s):
    global log_level
    log = logging.getLogger(s)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s[%(filename)s:%(lineno)d(%(funcName)s)] %(message)s')
    file_handler = RotatingFileHandler(os.path.join(log_dir,  'ledserver_fpga.log'),
                                       maxBytes=1024 * 1024 * 5,
                                       backupCount=10)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    log.setLevel(log_level)
    return log





