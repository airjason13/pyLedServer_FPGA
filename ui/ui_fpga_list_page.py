from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QLine
from PyQt5.QtGui import QFont, QBrush, QColor
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton, QLineEdit, QAbstractScrollArea, QHBoxLayout

from fpga.fpga_clients import FPGAClient
from global_def import *
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import *


class FpgaListPage(QWidget):
    client_table_header_font_size = 24
    TEST_CONTROLS_ITEMS = "Frame_W:640;FRAME_H:480;R_Gain:1;G_Gain:1;B_Gain:1;R_Gamma:2.2;G_Gamma:2.2;B_Gamma:2.2"
    TEST_CONTROLS_ITEMS_ERROR = "Frame_W:640;FRAME_H:420;R_Gain:1;G_Gain:1;B_Gain:1;R_Gamma:2.2;G_Gamma:2.2;B_Gamma:2.2"

    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, fpga_list: [], **kwargs):
        super(FpgaListPage, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.name = _name
        self.test_btn = None
        self.label_name = None
        self.layout = None
        self.client_table_widget = QTableWidget()
        self.client_media_setting_widget = None
        self.init_ui()

    def init_ui(self):
        self.label_name = QLabel(self.frame)
        self.label_name.setFixedSize(320, 64)
        self.label_name.setAlignment(Qt.AlignLeft)
        self.label_name.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.label_name.setText(self.name)
        self.client_table_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        # re-scan button
        self.rescan_btn = QPushButton(self.frame)
        self.rescan_btn.setFixedSize(320, 64)
        self.rescan_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.rescan_btn.setText("   Re-Scan   ")
        self.rescan_btn.clicked.connect(self.func_rescan_btn)

        self.label_widget = QWidget()
        self.label_widget_layout = QHBoxLayout()
        self.label_widget_layout.setAlignment(Qt.AlignLeft)
        self.label_widget_layout.addWidget(self.label_name)
        self.label_widget_layout.addWidget(self.rescan_btn)
        self.label_widget.setLayout(self.label_widget_layout)

        self.client_table_widget.setColumnCount(4)
        self.client_table_widget.setRowCount(0)
        self.client_table_widget.horizontalHeader().setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.client_table_widget.horizontalHeader().setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.client_table_widget.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_table_widget.setHorizontalHeaderLabels(['ID', 'VERSION', 'STATUS', 'CONTROLS'])
        # self.client_table_widget.setColumnWidth(0, 200)  # IP Column width:200
        # self.client_table_widget.setColumnWidth(1, 200)  # Version Column width:200
        self.client_table_widget.setColumnWidth(2, 240)
        self.client_table_widget.setColumnWidth(3, 1280)
            # self.client_table_widget.setColumnWidth(3, self.client_table_widget.width())

        self.client_media_setting_widget = QWidget()
        # Color Gain Value Setting
        self.red_gain_label = QLabel()
        self.red_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.red_gain_label.setText("Red Gain: ")
        self.red_gain_lineedit = QLineEdit()
        self.red_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.red_gain_lineedit.setText("1")

        self.green_gain_label = QLabel()
        self.green_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.green_gain_label.setText("Green Gain: ")
        self.green_gain_lineedit = QLineEdit()
        self.green_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.green_gain_lineedit.setText("1")

        self.blue_gain_label = QLabel()
        self.blue_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.blue_gain_label.setText("Blue Gain: ")
        self.blue_gain_lineedit = QLineEdit()
        self.blue_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.blue_gain_lineedit.setText("1")

        # Gamma Table Setting
        self.red_gamma_label = QLabel()
        self.red_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.red_gamma_label.setText("Red Gamma:")
        self.red_gamma_lineedit = QLineEdit()
        self.red_gamma_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.red_gamma_lineedit.setText("2.2")

        self.green_gamma_label = QLabel()
        self.green_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.green_gamma_label.setText("Green Gamma:")
        self.green_gamma_lineedit = QLineEdit()
        self.green_gamma_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.green_gamma_lineedit.setText("2.2")

        self.blue_gamma_label = QLabel()
        self.blue_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.blue_gamma_label.setText("Blue Gamma:")
        self.blue_gamma_lineedit = QLineEdit()
        self.blue_gamma_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.blue_gamma_lineedit.setText("2.2")

        # Frame Width/Height
        self.frame_width_label = QLabel()
        self.frame_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_width_label.setText("Frame Width:")
        self.frame_width_lineedit = QLineEdit()
        self.frame_width_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_width_lineedit.setText("640")

        self.frame_height_label = QLabel()
        self.frame_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_height_label.setText("Frame Width:")
        self.frame_height_lineedit = QLineEdit()
        self.frame_height_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_height_lineedit.setText("480")



        self.set_params_btn = QPushButton(self.frame)
        # self.set_params_btn.setFixedSize(320, 240)
        self.set_params_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.set_params_btn.setText("   SET   ")
        self.set_params_btn.clicked.connect(self.func_set_btn)

        self.client_media_setting_layout = QGridLayout()
        self.client_media_setting_layout.addWidget(self.red_gain_label, 0, 0)
        self.client_media_setting_layout.addWidget(self.red_gain_lineedit, 0, 1)
        self.client_media_setting_layout.addWidget(self.green_gain_label, 0, 2)
        self.client_media_setting_layout.addWidget(self.green_gain_lineedit, 0, 3)
        self.client_media_setting_layout.addWidget(self.blue_gain_label, 0, 4)
        self.client_media_setting_layout.addWidget(self.blue_gain_lineedit, 0, 5)

        self.client_media_setting_layout.addWidget(self.red_gamma_label, 1, 0)
        self.client_media_setting_layout.addWidget(self.red_gamma_lineedit, 1, 1)
        self.client_media_setting_layout.addWidget(self.green_gamma_label, 1, 2)
        self.client_media_setting_layout.addWidget(self.green_gamma_lineedit, 1, 3)
        self.client_media_setting_layout.addWidget(self.blue_gamma_label, 1, 4)
        self.client_media_setting_layout.addWidget(self.blue_gamma_lineedit, 1, 5)

        self.client_media_setting_layout.addWidget(self.frame_width_label, 2, 0)
        self.client_media_setting_layout.addWidget(self.frame_width_lineedit, 2, 1)

        self.client_media_setting_layout.addWidget(self.frame_height_label, 2, 2)
        self.client_media_setting_layout.addWidget(self.frame_height_lineedit, 2, 3)

        self.client_media_setting_layout.addWidget(self.set_params_btn, 2, 6)
        self.client_media_setting_widget.setLayout(self.client_media_setting_layout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label_widget)
        self.layout.addWidget(self.client_table_widget)
        self.layout.addWidget(self.client_media_setting_widget)
        self.setLayout(self.layout)


    def func_set_btn(self):
        log.debug("func test btn clicked")

    def func_rescan_btn(self):
        log.debug("func test btn clicked")

    def sync_clients_table(self, fpga_list: []):
        if len(fpga_list) == 0:
            log.debug("no fpga")
            return

        row_count = self.client_table_widget.rowCount()
        for i in range(row_count):
            row_to_remove = self.client_table_widget.rowAt(i)
            self.client_table_widget.removeRow(row_to_remove)

        for fpga in fpga_list:
            row_count = self.client_table_widget.rowCount()
            self.client_table_widget.insertRow(row_count)
            self.client_table_widget.setItem(row_count, 0, QTableWidgetItem(str(fpga.i_id)))
            self.client_table_widget.setItem(row_count, 1, QTableWidgetItem(fpga.s_version))
            self.client_table_widget.setItem(row_count, 2, QTableWidgetItem(str(fpga.i_status)))
            if row_count == 3:
                self.client_table_widget.setItem(row_count, 3, QTableWidgetItem(self.TEST_CONTROLS_ITEMS_ERROR))
            else:
                self.client_table_widget.setItem(row_count, 3, QTableWidgetItem(self.TEST_CONTROLS_ITEMS))


        self.client_table_widget.item(3,3).setForeground(QBrush(QColor(255, 0, 0)))