import qdarkstyle
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QMessageBox, QGridLayout, QFrame, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QProgressBar
from global_def import log
from qt_ui_style.button_qss import QFont_Style_Default, QFont_Style_Size_L


class VProgressDialog(QWidget):
    def __init__(self, win_title="Info", win_w=800, win_h=240, label_str="", process_range=100):
        super(VProgressDialog, self).__init__()
        self.setWindowTitle(win_title)
        self.resize(QSize(win_w, win_h))
        self.win_w = win_w
        self.win_h = win_h
        self.label_str = label_str
        self.info_label = None
        self.process_bar = None
        self.process_range = process_range
        self.process_value = 0
        self.vertical_layout = None
        self.ok_btn = None
        self.init_ui()

    def init_ui(self):

        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.info_label = QLabel()
        self.info_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.info_label.setText(self.label_str)

        self.process_bar = QProgressBar()
        self.process_bar.setRange(0, self.process_range)
        self.process_bar.setValue(self.process_value)
        # log.debug("VProgressDialog geometry(): %s", self.geometry())
        # self.process_bar.setFixedSize(self.win_w, int(self.win_h/4))
        self.process_bar.setFixedHeight(int(self.win_h/4))

        self.ok_btn = QPushButton()
        self.ok_btn.setText("OK")
        # self.ok_btn.setFixedSize(self.win_w, int(self.win_h / 4))
        self.ok_btn.setFixedHeight(int(self.win_h / 4))

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.info_label)
        self.vertical_layout.addWidget(self.process_bar)
        self.vertical_layout.addWidget(self.ok_btn)
        self.setLayout(self.vertical_layout)
        log.debug("End of init_ui")
        # log.debug("VProgressDialog geometry(): %s", self.geometry())

    def set_label_text(self, lstr: str):
        self.label_str = lstr
        self.info_label.setText(self.label_str)

    def set_process_value(self, value):
        if 0 < value < self.process_range:
            pass
        else:
            log.debug("value : %d, range: %d", value, self.process_range)
        self.process_value = value
        self.process_bar.setValue(value)

    def closeEvent(self, a0):
        log.debug("close VProgressDialog")


