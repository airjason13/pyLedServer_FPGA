import random
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton
from global_def import *
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import *
from FPGA_protocol.protocol2 import FPGAJsonParams, fpga_test_value, fpga_test_layout_value


class TestPage(QWidget):
    pyqt_signal_rw_single_run_completed = pyqtSignal()
    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, **kwargs):
        super(TestPage, self).__init__()
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.name = _name
        self.test_btn = None
        self.label_name = None
        self.layout = None
        self.fpga_list = kwargs.get("fpga_list")
        self.fpga_cmd_center = kwargs.get("fpga_cmd_center")

        '''test count'''
        self.utc_test_count = 0
        self.write_count = 0
        self.write_fail_count = 0
        self.read_count = 0
        self.read_fail_count = 0
        self.test_opt_index = 0     # 第幾組測試參數
        self.test_timer = None

        self.init_ui()

    def reset_total_test_count(self):
        self.utc_test_count = 0
        self.write_count = 0
        self.write_fail_count = 0
        self.read_count = 0
        self.read_fail_count = 0

    def init_ui(self):
        self.Load_test_value_label = QLabel(self.frame)
        self.Load_test_value_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.Load_test_value_label.setText("Read/Write Test to FPGA")
        self.read_write_test_result_label = QLabel(self.frame)
        self.read_write_test_result_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.read_write_test_result_label.setText("Read/Write Res:")
        self.Load_test_value_label_btn = QPushButton(self.frame)
        self.Load_test_value_label_btn.setFixedSize(128, 64)
        self.Load_test_value_label_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.Load_test_value_label_btn.setText("Start")
        self.Load_test_value_label_btn.clicked.connect(self.Load_test_value_label_btn_clicked)
        self.layout = QGridLayout()
        self.layout.addWidget(self.Load_test_value_label, 1, 0)
        self.layout.addWidget(self.Load_test_value_label_btn, 1, 1)
        self.layout.addWidget(self.read_write_test_result_label, 2, 0)

        self.setLayout(self.layout)
        # self.frame.layout().addWidget(self)

    def Load_test_value_label_btn_clicked(self):
        log.debug("func func_fpga_load_default_valule clicked")
        self.reset_total_test_count()

        self.pyqt_signal_rw_single_run_completed.connect(self.rw_test_signal_run_completed)
        self.test_timer = QTimer(self)
        self.test_timer.timeout.connect(self.rw_test_to_fpga)
        self.test_timer.start(240 * 1000)

        # self.write_test_value_to_fpga()
        self.rw_test_to_fpga()


    def write_test_value_to_fpga(self, test_opt_index=0):
        test_opt_index = 0
        for i in range(FPGA_START_ID, FPGA_START_ID + len(self.fpga_list)):
            for test_item, value in fpga_test_value[test_opt_index].items():
                log.debug("id: %d, test_item : %s, value : %s", i, test_item, value)
                if value is not None:
                    ret = self.fpga_cmd_center.write_fpga_register(i, test_item, value)
                    if ret < 0:
                        log.debug("write register failed!")
                        self.write_fail_count += 1
                self.write_count += 1
            for test_item, value in fpga_test_layout_value[test_opt_index].items():
                if value is not None:
                    for port_id in range(64):
                        ret = self.fpga_cmd_center.write_fpga_register(
                            i, "{}{}{}".format(test_item, "_p", str(port_id)), value)
                        if ret < 0:
                            log.debug("write layout register failed, fpga_id: %d, port_id: %d: ", i, port_id)
                            log.debug("register name : %s", "{}{}{}".format(test_item, "_p", port_id))
                        self.write_count += 1
                        time.sleep(0.05)

    def rw_test_to_fpga(self):
        test_opt_index = self.test_opt_index
        # handle write
        for i in range(FPGA_START_ID, FPGA_START_ID + len(self.fpga_list)):
            for test_item, value in fpga_test_value[test_opt_index].items():
                if value is not None:
                    ret = self.fpga_cmd_center.write_fpga_register(i, test_item, value)
                    if ret < 0:
                        log.debug("write register failed!")
                        self.write_fail_count += 1
                    self.write_count += 1

            for test_item, value in fpga_test_layout_value[test_opt_index].items():
                if value is not None:
                    for port_id in range(64):
                        ret = self.fpga_cmd_center.write_fpga_register(
                            i, "{}{}{}".format(test_item, "_p", str(port_id)), value)
                        if ret == 0:
                            # log.debug("write layout register ok, fpga_id: %d, port_id: %d: ", i, port_id)
                            pass
                        else:
                            log.debug("write layout register failed, fpga_id: %d, port_id: %d: ", i, port_id)
                            log.debug("register name : %s", "{}{}{}".format(test_item, "_p", port_id))
                            self.write_fail_count += 1
                        self.write_count += 1
                        time.sleep(0.05)
        # read for check

        time.sleep(1)
        for i in range(FPGA_START_ID, FPGA_START_ID + len(self.fpga_list)):
            for test_item, value in fpga_test_value[test_opt_index].items():
                if value is not None:
                    ret, int_r_value = self.fpga_cmd_center.read_fpga_register(i, test_item)
                    if ret == 0 and str(int_r_value) == value:
                        log.debug("read %s ok!", test_item)
                        # pass
                    else:
                        if int_r_value is None:
                            int_r_value = -1
                        log.debug("read %s, int_r_value: %d, value:%s !NG!", test_item, int_r_value, value)
                        self.read_fail_count += 1
                    self.read_count += 1

            for test_item, value in fpga_test_layout_value[test_opt_index].items():
                if value is not None:
                    for port_id in range(64):
                        ret, int_r_value = self.fpga_cmd_center.read_fpga_register(
                            i, "{}{}{}".format(test_item, "_p", str(port_id)))
                        if ret == 0 and str(int_r_value) == value:
                            # log.debug("read %s ok!", test_item)
                            pass
                        else:
                            log.debug("write layout register failed, fpga_id: %d, port_id: %d: ", i, port_id)
                            log.debug("register name : %s", "{}{}{}".format(test_item, "_p", port_id))
                            self.read_fail_count += 1
                        self.read_count += 1
                        time.sleep(0.05)

        self.test_opt_index += 1
        if self.test_opt_index > 1:
            self.test_opt_index = 0

        self.pyqt_signal_rw_single_run_completed.emit()

    def rw_test_signal_run_completed(self):
        log.debug("self.write_count : %d, self.write_fail_count : %d", self.write_count, self.write_fail_count)
        log.debug("self.read_count : %d, self.read_fail_count : %d", self.read_count, self.read_fail_count)
        str_text = "write_count : {}, fail_count : {} \nread_count : {}, read_fail_count : {}".format(
            self.write_count, self.write_fail_count, self.read_count, self.read_fail_count)
        self.read_write_test_result_label.setText(str_text)

    def utc_test(self):
        log.debug("self.utc_test_count : %d", self.utc_test_count)
        self.utc_test_count += 1
        s_utc_temp = str(random.randint(1000, 9999))
        for i in range(2, 4):   # send cmd to id 2/3
            start_time = time.time()
            ret = self.fpga_cmd_center.write_fpga_register(i, "UTC", s_utc_temp)
            log.debug("write time : %f", time.time() - start_time)
            log.debug("write fpga id:%d UTC ret : %d", i, ret)
        for i in range(2, 4):   # read cmd to id 2/3
            start_time = time.time()
            ret, id_utc = self.fpga_cmd_center.read_fpga_register(i, "UTC")
            log.debug("read time : %f", time.time() - start_time)
            if ret == 0:
                if s_utc_temp == str(id_utc):
                    log.debug("read OK")
                else:
                    log.debug("UTC read/write failed!")
            else:
                log.debug("UTC read/write failed!")

