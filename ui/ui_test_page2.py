import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton

from ext_qt_widgets.playing_preview_widget import PlayingPreviewWindow
from global_def import *
from media_engine import media_engine
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import *
from PyQt5.QtCore import QThread, pyqtSignal


class TestPage2(QWidget):
    pyqt_signal_rw_single_run_completed = pyqtSignal()

    def __init__(self, _main_window, _frame: QWidget, _name: str, **kwargs):
        super(TestPage2, self).__init__()
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.name = _name
        self.label_name = None
        self.layout = None
        self.init_ui()

    def init_ui(self):
        self.label_name = QLabel(self.name)
        self.layout = QVBoxLayout(self)
