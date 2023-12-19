from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton
from global_def import *
from qt_ui_style.button_qss import *


class TestPage(QWidget):

    def __init__(self, _main_window, _frame: QWidget, _name, **kwargs):
        super(TestPage, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.name = _name
        self.test_btn = None
        self.label_name = None
        self.layout = None
        self.init_ui()

    def init_ui(self):
        self.label_name = QLabel(self.frame)
        self.label_name.setFixedSize(320, 240)
        self.label_name.setFont(QFont(QFont_Style_Default, QFont_Style_Size_XL))
        self.label_name.setText(self.name)
        self.test_btn = QPushButton(self.frame)
        self.test_btn.setFixedSize(320, 240)
        self.test_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_XL))
        self.test_btn.setText(self.name)
        self.test_btn.clicked.connect(self.func_test_btn)
        self.layout = QGridLayout()
        self.layout.addWidget(self.label_name, 0, 1)
        self.layout.addWidget(self.test_btn, 1, 2)
        self.setLayout(self.layout)
        # self.frame.layout().addWidget(self)

    def func_test_btn(self):
        log.debug("func test btn clicked")
