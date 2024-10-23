import time
from datetime import datetime

from PyQt5.QtCore import QObject, Qt, QTimer
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QFrame, QLabel
from PyQt5 import QtGui
from qt_ui_style.button_qss import *
from global_def import *
from ext_qt_widgets.qround_progress_bar import QRoundProgressBar
import psutil


class UiSystemSoftware(QWidget):

    CPU_USAGE_MIN = 0
    CPU_USAGE_DEFAULT = 100
    CPU_USAGE_MAX = 100
    CIRCLE_PROGRESS_DEFAULT_WIDTH = 300
    CIRCLE_PROGRESS_DEFAULT_HEIGHT = 300
    CPU_USAGE_CIRCULAR_PROGRESS_NAME = "cpu_usage_circular_progress"
    MEM_USAGE_CIRCULAR_PROGRESS_NAME = "mem_usage_circular_progress"
    temperature_log = utils.log_utils.logging_init(__file__, "temperature.log")

    def __init__(self, _main_window, _frame: QWidget, **kwargs):

        super(UiSystemSoftware, self).__init__(**kwargs)

        self.main_windows = _main_window
        self.frame = _frame
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            self.machine_arch = "aarch64"
        else:
            self.machine_arch = "x86"

        root_dir = os.path.dirname(sys.modules['__main__'].__file__)
        led_config_dir = os.path.join(root_dir, 'log')
        self.temperature_log_file_uri = os.path.join(led_config_dir, "temperature.log")

        self.temperature_now = 0
        self.max_temperature, self.max_temperature_time = self.get_history_max_temp()

        self.frame_cpu_usage_circular_progress = None
        self.frame_mem_usage_circular_progress = None
        self.circular_progress_list = []

        self.label_temperature = None

        self.vertical_layout = None

        self.init_ui_system_usage()

        self.cpu_percent = 0
        self.ram_percent = 0

        self.update_usage_timer = QTimer()
        self.update_usage_timer.timeout.connect(self.update_cpu_ram_usage)
        self.update_usage_timer.start(1000)
        log.debug("")

    def init_ui_system_usage(self):

        self.frame_cpu_usage_circular_progress = QRoundProgressBar()
        self.frame_cpu_usage_circular_progress.set_name(self.CPU_USAGE_CIRCULAR_PROGRESS_NAME)
        self.circular_progress_list.append(self.frame_cpu_usage_circular_progress)
        self.frame_mem_usage_circular_progress = QRoundProgressBar()
        self.frame_mem_usage_circular_progress.set_name(self.MEM_USAGE_CIRCULAR_PROGRESS_NAME)
        self.circular_progress_list.append(self.frame_mem_usage_circular_progress)
        self.vertical_layout = QVBoxLayout()

        for cp in self.circular_progress_list:
            cp.setBaseSize(self.CIRCLE_PROGRESS_DEFAULT_WIDTH, self.CIRCLE_PROGRESS_DEFAULT_HEIGHT)
            cp.setDataPenWidth(0)
            cp.setOutlinePenWidth(0)
            cp.setDonutThicknessRatio(0.85)

            if cp.name == self.CPU_USAGE_CIRCULAR_PROGRESS_NAME:
                cp.set_tag('CPU Usage: \n')
                cp.setFormat(' %v %')
                cp.setRange(self.CPU_USAGE_MIN, self.CPU_USAGE_MAX)
                cp.setValue(self.CPU_USAGE_DEFAULT)
            elif cp.name == self.MEM_USAGE_CIRCULAR_PROGRESS_NAME:
                cp.set_tag('MEM Usage: \n')
                cp.setFormat(' %v %')
                cp.setRange(self.CPU_USAGE_MIN, self.CPU_USAGE_MAX)
                cp.setValue(self.CPU_USAGE_DEFAULT)
            cp.setDecimals(1)
            cp.setNullPosition(90)

            cp.setBarStyle(QRoundProgressBar.StyleDonut)
            cp.setDataColors([(0., QtGui.QColor.fromRgb(128, 196, 0)),
                              (0.5, QtGui.QColor.fromRgb(196, 128, 0)),
                              (1., QtGui.QColor.fromRgb(255, 0, 0))])

            self.vertical_layout.addWidget(cp)

        self.label_temperature = QLabel(self)
        self.label_temperature.setText("Temp:--")
        self.vertical_layout.addWidget(self.label_temperature)

        self.setLayout(self.vertical_layout)
        self.frame.layout().addWidget(self)

    def update_cpu_ram_usage(self):
        self.cpu_percent = psutil.cpu_percent()
        self.ram_percent = psutil.virtual_memory().percent

        self.frame_cpu_usage_circular_progress.setValue(self.cpu_percent)
        self.frame_mem_usage_circular_progress.setValue(self.ram_percent)

        if "aarch64" in self.machine_arch:
            temp_str = os.popen("vcgencmd measure_temp").read()
            self.label_temperature.setText(temp_str)
            self.temperature_now = temp_str.strip().split("=")[1].split(".")[0]
            if int(self.temperature_now) > int(self.max_temperature):
                self.max_temperature_time = datetime.now()
                self.max_temperature = self.temperature_now
                # write temp log
                with open(self.temperature_log_file_uri, "w") as f:
                    data = "max_temp:{};time:{}".format(self.max_temperature, self.max_temperature_time)
                    f.write(data)
                    f.truncate()
                    f.close()
                    os.system('sync')

        # self.temperature_log.debug("max_temperature: %d", 88)

    def get_history_max_temp(self):
        max_temperature = 0
        max_temperature_time = time.time()
        if os.path.exists(self.temperature_log_file_uri):
            with open(self.temperature_log_file_uri, "r") as f:
                lines = f.readlines()
            f.close()
            for line in lines:
                if "max_temp" in line:
                    max_temperature = line.strip().split(";")[0].split(":")[1]
                    max_temperature_time = line.strip().split(";")[1].split(":")[1]

        return max_temperature, max_temperature_time