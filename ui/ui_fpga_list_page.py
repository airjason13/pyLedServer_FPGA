import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QLine, QTimer
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
        self.fpga_list = fpga_list
        self.init_ui()

        '''for test'''
        self.cmd_test_timer = QTimer()
        self.frame_res_test_count = 0

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
        self.cmd_test_timer.timeout.connect(self.fpga_write_flash_test)
        self.cmd_test_timer.start(3 * 1000)

    def func_rescan_btn(self):
        log.debug("func rescan btn clicked")

    def sync_clients_table(self, fpga_list: []):
        if len(fpga_list) == 0:
            log.debug("no fpga")
            return
        log.debug("sync_clients_table")
        self.fpga_list = fpga_list
        row_count = self.client_table_widget.rowCount()
        for i in range(row_count):
            row_to_remove = self.client_table_widget.rowAt(i)
            self.client_table_widget.removeRow(row_to_remove)

        for fpga in self.fpga_list:
            row_count = self.client_table_widget.rowCount()
            self.client_table_widget.insertRow(row_count)
            self.client_table_widget.setItem(row_count, 0, QTableWidgetItem(str(fpga.i_id)))
            self.client_table_widget.setItem(row_count, 1, QTableWidgetItem(fpga.s_version))
            self.client_table_widget.setItem(row_count, 2, QTableWidgetItem(str(fpga.i_status)))
            if row_count == 3:
                self.client_table_widget.setItem(row_count, 3, QTableWidgetItem(self.TEST_CONTROLS_ITEMS_ERROR))
            else:
                self.client_table_widget.setItem(row_count, 3, QTableWidgetItem(self.TEST_CONTROLS_ITEMS))

        # self.client_table_widget.item(3,3).setForeground(QBrush(QColor(255, 0, 0)))

    def cmd_frame_res_test(self):
        log.debug("self.frame_res_test_count : %d", self.frame_res_test_count)
        self.frame_res_test_count += 1
        s_width_temp = str(640)
        s_height_temp = str(480)
        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            start_time = time.time()
            ret = self.fpga_list[i].write_cmd("frameWidth", s_width_temp)
            ret = self.fpga_list[i].write_cmd("frameHeight", s_height_temp)
            # ret = self.fpga_cmd_center.write_fpga_register(i, "frameWidth", s_width_temp)
            # ret = self.fpga_cmd_center.write_fpga_register(i, "frameHeight", s_height_temp)
            log.debug("write time : %f", time.time() - start_time)
            log.debug("write fpga id:%d UTC ret : %d", i, ret)
        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            start_time = time.time()
            ret, id_width = self.fpga_list[i].read_cmd("frameWidth")
            ret, id_height = self.fpga_list[i].read_cmd("frameHeight")
            # ret, id_width = self.fpga_cmd_center.read_fpga_register(i, "frameWidth")

            if ret == 0:
                if s_width_temp == str(id_width) and s_height_temp == str(id_height):
                    log.debug("read OK")
                    log.debug("read fpga id:%d UTC ret : %d, id%d_framewidth : %s", i, ret, i, id_width)
                    log.debug("read fpga id:%d UTC ret : %d, id%d_frameheight : %s", i, ret, i, id_height)
                else:
                    log.debug("UTC read/write failed!")
            else:
                log.debug("UTC read/write failed!")

    def fpga_write_flash_test(self):
        log.debug("self.frame_res_test_count : %d", self.frame_res_test_count)
        self.frame_res_test_count += 1
        self.main_windows.fpga_cmd_center.set_fpga_write_flash()
        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            start_time = time.time()
            ret, id_width = self.fpga_list[i].read_cmd("frameWidth")
            if ret == 0:
                log.debug("id: %d, id_width: %s", self.fpga_list[i].i_id, id_width)
                if int(id_width) != 640:
                    log.fatal("id: %d, read frame width : %s, not match test frame width",
                              self.fpga_list[i].i_id, id_width )
            ret, id_height = self.fpga_list[i].read_cmd("frameHeight")
            if ret == 0:
                if int(id_height) != 480:
                    log.debug("id: %d, id_height: %s", self.fpga_list[i].i_id, id_height)
                    log.fatal("id: %d, read frame height : %s, not match test frame height",
                              self.fpga_list[i].i_id, id_width)