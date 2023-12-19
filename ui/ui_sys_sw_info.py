from PyQt5.QtCore import QObject, Qt, QTimer
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QFrame
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

    def __init__(self, _main_window, _frame: QWidget, **kwargs):

        super(UiSystemSoftware, self).__init__(**kwargs)

        self.main_windows = _main_window
        self.frame = _frame
        # self.widget = QWidget(self.frame)
        self.frame_cpu_usage_circular_progress = None
        self.frame_mem_usage_circular_progress = None
        self.circular_progress_list = []
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
        self.setLayout(self.vertical_layout)
        self.frame.layout().addWidget(self)

    def update_cpu_ram_usage(self):
        self.cpu_percent = psutil.cpu_percent()
        self.ram_percent = psutil.virtual_memory().percent

        self.frame_cpu_usage_circular_progress.setValue(self.cpu_percent)
        self.frame_mem_usage_circular_progress.setValue(self.ram_percent)
