from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget
from qt_ui_style.button_qss import *
from qt_ui_style.frame_style import *
from global_def import *


class UiFuncFrame(QWidget):

    qtsignal_page_selector = pyqtSignal(str)

    def __init__(self, _main_window, _frame, _btn_name_list: list[str], _slot_func_btn=None,  **kwargs):
        super(UiFuncFrame, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame     # self.main_windows.left_top_frame

        self.btn_name_list = _btn_name_list
        if _slot_func_btn is not None:
            self.slot_func_btn = _slot_func_btn
        else:
            self.slot_func_btn = None

        self.btn_total_num = len(self.btn_name_list)
        self.btn_list = []
        self.vertical_layout = None
        self.init_ui()

        self.qtsignal_page_selector.connect(self.main_windows.slot_right_frame_page_changed)

    def init_ui(self):
        self.init_ui_pushbutton()
        self.frame.setFixedSize(QPushButton_Page_Selector_Min_Width + QWidget_Margin,
                                (self.btn_total_num + 1) * QPushButton_Page_Selector_Min_Height + QWidget_Margin)

    def init_ui_pushbutton(self):
        log.debug("init_ui_pushbutton")
        for i in range(self.btn_total_num):
            btn = QPushButton(self.frame)
            btn.setObjectName(self.btn_name_list[i])
            btn.setText(self.btn_name_list[i])
            self.btn_list.append(btn)

        self.vertical_layout = QVBoxLayout()

        for btn in self.btn_list:
            self.vertical_layout.addWidget(btn)

        self.setLayout(self.vertical_layout)

        '''set btn/font style and size'''
        for btn in self.findChildren(QPushButton):
            btn.setStyleSheet(QPushButton_Style)
            btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_XL))
            btn.clicked.connect(self.btn_clicked_func)
            print("self.btn_clicked_func :", self.btn_clicked_func)

        self.frame.layout().addWidget(self)

    def btn_clicked_func(self):
        log.debug("btn_clicked_func %s", self.sender().text())
        self.qtsignal_page_selector.emit(self.sender().text())





