import logging
import time

import qdarkstyle
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QLine, QTimer
from PyQt5.QtGui import QFont, QBrush, QColor
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton, QLineEdit, QAbstractScrollArea, QHBoxLayout, QMenu, QAction, QMessageBox

from ext_qt_widgets.fpga_ota_file_select_dialog import GetFPGAOTADialog
from ext_qt_widgets.fpga_test_window import FPGARegWindow
from ext_qt_widgets.gen_fpga_config_json_dialog import GenFPGAConfigJsonDialog
from ext_qt_widgets.get_fpga_config_dialog import GetFPGAConfigDialog
from fpga.fpga_clients import FPGAClient
from global_def import *
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import *
from qt_ui_style.set_qstyle import set_qstyle_dark
from utils.utils_file_access import get_fpga_config_file_list, load_fpga_json_file, get_fpga_ota_file_list, \
    get_led_config_from_file_uri
import json
from FPGA_protocol.protocol2 import dataAddressDict


class FpgaListPage(QWidget):
    client_table_header_font_size = 24
    TEST_CONTROLS_ITEMS = "Frame_W:640;FRAME_H:480;R_Gain:1;G_Gain:1;B_Gain:1;R_Gamma:2.2;G_Gamma:2.2;B_Gamma:2.2"
    TEST_CONTROLS_ITEMS_ERROR = "Frame_W:640;FRAME_H:420;R_Gain:1;G_Gain:1;B_Gain:1;R_Gamma:2.2;G_Gamma:2.2;B_Gamma:2.2"

    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, fpga_list: [], **kwargs):
        super(FpgaListPage, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.media_engine = media_engine
        self.name = _name
        self.fpga_total_num = self.main_windows.fpga_total_num
        self.test_btn = None
        self.label_name = None
        self.rescan_btn = None

        self.gen_json_file_btn = None
        self.gen_fpga_config_file_dialog = None

        self.set_fpga_with_config_json_file_btn = None
        self.get_fpga_config_json_file_dialog = None

        self.select_fpga_ota_file_dialog = None

        self.fpga_write_flash_btn = None
        self.fpga_read_flash_btn = None
        self.fpga_set_gamma_table_btn = None

        self.label_widget = None
        self.label_widget_layout = None
        self.red_gain_label = None
        self.red_gain_lineedit = None
        self.green_gain_label = None
        self.green_gain_lineedit = None
        self.blue_gain_label = None
        self.blue_gain_lineedit = None

        # Gamma Table Setting
        self.rgb_gamma_label = None
        self.rgb_gamma_lineedit = None

        # Frame Width/Height
        self.frame_width_label = None
        self.frame_width_lineedit = None

        self.frame_height_label = None
        self.frame_height_lineedit = None

        self.set_params_btn = None

        self.client_media_setting_layout = None
        self.layout = None
        self.client_table_widget = QTableWidget()
        self.client_media_setting_widget = None
        self.right_click_select_fpga = None
        self.fpga_list = fpga_list
        self.show_register_window = []
        self.init_ui()

        # 開啟右鍵選單功能
        self.client_table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.client_table_widget.customContextMenuRequested.connect(self.clients_menu_context_tree)

        '''for test'''
        self.cmd_test_timer = QTimer()
        self.frame_res_test_count = 0

        self.media_engine.led_video_params.install_video_params_changed_slot(self.video_params_changed)

    def init_ui(self):
        self.label_name = QLabel(self.frame)
        self.label_name.setFixedSize(240, 64)
        self.label_name.setAlignment(Qt.AlignLeft)
        self.label_name.setFont(QFont(QFont_Style_Default, QFont_Style_Size_XL))
        self.label_name.setText(self.name)
        self.client_table_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        # re-scan button
        self.rescan_btn = QPushButton(self.frame)
        self.rescan_btn.setFixedSize(140, 64)
        self.rescan_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.rescan_btn.setText("   Re-Scan   ")
        self.rescan_btn.clicked.connect(self.func_rescan_btn)

        # generate fpga config json file button
        self.gen_json_file_btn = QPushButton(self.frame)
        self.gen_json_file_btn.setFixedSize(240, 64)
        self.gen_json_file_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.gen_json_file_btn.setText("Gen Config File")
        self.gen_json_file_btn.clicked.connect(self.func_gen_fpga_config_file_btn)

        # set config file to fpga
        self.set_fpga_with_config_json_file_btn = QPushButton(self.frame)
        self.set_fpga_with_config_json_file_btn.setFixedSize(320, 64)
        self.set_fpga_with_config_json_file_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.set_fpga_with_config_json_file_btn.setText("Set FPGA with Config")
        self.set_fpga_with_config_json_file_btn.clicked.connect(self.func_set_fpga_with_config_file_btn)

        self.fpga_write_flash_btn = QPushButton()
        self.fpga_write_flash_btn.setFixedSize(180, 64)
        self.fpga_write_flash_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.fpga_write_flash_btn.setText("Write Flash")
        self.fpga_write_flash_btn.clicked.connect(self.func_fpga_write_flash_btn)
        self.fpga_read_flash_btn = QPushButton()
        self.fpga_read_flash_btn.setFixedSize(180, 64)
        self.fpga_read_flash_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.fpga_read_flash_btn.setText("Read Flash")
        self.fpga_read_flash_btn.clicked.connect(self.func_fpga_read_flash_btn)

        self.fpga_set_gamma_table_btn = QPushButton()
        self.fpga_set_gamma_table_btn.setFixedSize(240, 64)
        self.fpga_set_gamma_table_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.fpga_set_gamma_table_btn.setText("Set Gamma Table")
        self.fpga_set_gamma_table_btn.clicked.connect(self.func_fpga_set_gamma_table_btn)

        self.label_widget = QWidget()
        self.label_widget_layout = QHBoxLayout()
        self.label_widget_layout.setAlignment(Qt.AlignLeft)
        self.label_widget_layout.addWidget(self.label_name)
        self.label_widget_layout.addWidget(self.rescan_btn)
        self.label_widget_layout.addWidget(self.gen_json_file_btn)
        self.label_widget_layout.addWidget(self.set_fpga_with_config_json_file_btn)
        self.label_widget_layout.addWidget(self.fpga_write_flash_btn)
        self.label_widget_layout.addWidget(self.fpga_read_flash_btn)
        self.label_widget_layout.addWidget(self.fpga_set_gamma_table_btn)
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
        self.rgb_gamma_label = QLabel()
        self.rgb_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.rgb_gamma_label.setText("Red Gamma:")
        self.rgb_gamma_lineedit = QLineEdit()
        self.rgb_gamma_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        str_gamma_index = get_led_config_from_file_uri("led_parameters", "led_gamma")
        log.debug("str_gamma_index : %s", str_gamma_index[0])
        self.rgb_gamma_lineedit.setText(str_gamma_index[0])

        # Frame Width/Height
        self.frame_width_label = QLabel()
        self.frame_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_width_label.setText("Frame Width:")
        self.frame_width_lineedit = QLineEdit()
        self.frame_width_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        # str_frame_width, str_frame_height = get_led_config_from_file_uri("led_wall_resolution",
        #                                                                 "led_wall_width", "led_wall_height")
        str_frame_width, str_frame_height = self.media_engine.led_video_params.get_output_frame_res_str()
        log.debug("str_frame_width : %s, str_frame_height : %s", str_frame_width, str_frame_height)
        self.frame_width_lineedit.setText(str_frame_width)

        self.frame_height_label = QLabel()
        self.frame_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_height_label.setText("Frame Width:")
        self.frame_height_lineedit = QLineEdit()
        self.frame_height_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.frame_height_lineedit.setText(str_frame_height)

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

        self.client_media_setting_layout.addWidget(self.rgb_gamma_label, 1, 4)
        self.client_media_setting_layout.addWidget(self.rgb_gamma_lineedit, 1, 5)

        self.client_media_setting_layout.addWidget(self.frame_width_label, 1, 0)
        self.client_media_setting_layout.addWidget(self.frame_width_lineedit, 1, 1)

        self.client_media_setting_layout.addWidget(self.frame_height_label, 1, 2)
        self.client_media_setting_layout.addWidget(self.frame_height_lineedit, 1, 3)

        self.client_media_setting_layout.addWidget(self.set_params_btn, 1, 6)
        self.client_media_setting_widget.setLayout(self.client_media_setting_layout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label_widget)
        self.layout.addWidget(self.client_table_widget)
        self.layout.addWidget(self.client_media_setting_widget)
        self.setLayout(self.layout)

    def func_set_btn(self):
        log.debug("func test btn clicked")
        if self.media_engine.led_video_params.get_led_red_gain() != int(self.red_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_red_gain(int(self.red_gain_lineedit.text()))
        if self.media_engine.led_video_params.get_led_green_gain() != int(self.green_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_green_gain(int(self.green_gain_lineedit.text()))
        if self.media_engine.led_video_params.get_led_blue_gain() != int(self.blue_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_blue_gain(int(self.blue_gain_lineedit.text()))

        if self.media_engine.led_video_params.get_led_gamma() != float(self.rgb_gamma_lineedit.text()):
            self.media_engine.led_video_params.set_led_gamma(float(self.rgb_gamma_lineedit.text()))

        if self.media_engine.led_video_params.get_output_frame_width() != int(self.frame_width_lineedit.text()):
            self.media_engine.led_video_params.set_output_frame_width(int(self.frame_width_lineedit.text()))

        if self.media_engine.led_video_params.get_output_frame_width() != int(self.frame_width_lineedit.text()):
            self.media_engine.led_video_params.set_output_frame_width(int(self.frame_width_lineedit.text()))

        if self.media_engine.led_video_params.get_output_frame_height() != int(self.frame_height_lineedit.text()):
            self.media_engine.led_video_params.set_output_frame_height(int(self.frame_height_lineedit.text()))

        # below is for test use
        # self.cmd_test_timer.timeout.connect(self.fpga_write_flash_test)
        # self.cmd_test_timer.timeout.connect(self.fpga_read_flash_test)
        # self.cmd_test_timer.start(3 * 1000)

    def func_fpga_set_gamma_table_btn(self):
        if len(self.fpga_list) == 0:
            self.show_info_message_box("Info", "No FPGA Online!")
            return
        self.func_rescan_btn()
        self.main_windows.init_fpga_gamma()
        if len(self.fpga_list) == 1:
            self.show_info_message_box("Info", "Set Gamma Table on {} FPGA OK!".format(len(self.fpga_list)))
        else:
            self.show_info_message_box("Info", "Set Gamma Table on {} FPGAs OK!".format(len(self.fpga_list)))

    def func_rescan_btn(self):
        log.debug("func_rescan_btn")
        row_count = self.client_table_widget.rowCount()
        for i in reversed(range(row_count)):
            row_to_remove = self.client_table_widget.rowAt(i)
            self.client_table_widget.removeRow(row_to_remove)
        log.debug("rescan start")

        self.main_windows.fpga_cmd_center.set_fpga_id_broadcast(FPGA_START_ID)
        self.main_windows.fpga_list = []
        self.main_windows.fpga_total_num = self.main_windows.get_fpga_total_num()
        self.fpga_total_num = self.main_windows.fpga_total_num
        log.debug("self.fpga_total_num : %d", self.fpga_total_num)
        for i in range(FPGA_START_ID, FPGA_START_ID + self.fpga_total_num):
            log.debug("scan fpga id : %d", i)
            fpga_tmp = FPGAClient(i, self.main_windows.fpga_cmd_center)
            self.main_windows.fpga_list.append(fpga_tmp)
        self.fpga_list = self.main_windows.fpga_list
        self.sync_clients_table(self.fpga_list)
        log.debug("func_rescan_btn end")

    def func_fpga_write_flash_btn(self):
        if len(self.fpga_list) == 0:
            self.show_info_message_box("Info", "No FPGA Online!")
            return
        self.main_windows.fpga_cmd_center.set_fpga_write_flash()
        time.sleep(5)
        # 需補dialog
        # log.debug("need a ok dialog")
        self.show_info_message_box("Info", "Write Flash OK!")

    def func_fpga_read_flash_btn(self):
        if len(self.fpga_list) == 0:
            self.show_info_message_box("Info", "No FPGA Online!")
            return
        self.main_windows.fpga_cmd_center.set_fpga_read_flash()
        time.sleep(5)
        # 需補dialog
        # log.debug("need a ok dialog")
        self.show_info_message_box("Info", "Read Flash OK!")

    def func_gen_fpga_config_file_btn(self):
        log.debug("func func_gen_fpga_config_file_btn clicked")
        self.gen_fpga_config_file_dialog = None
        config_json_files_list = get_fpga_config_file_list(root_dir + '/fpga_config_jsons')
        self.gen_fpga_config_file_dialog = GenFPGAConfigJsonDialog(config_json_files_list)
        self.gen_fpga_config_file_dialog.signal_new_config_json_generate.connect(
            self.slot_gen_new_fpga_config_json_file)
        self.gen_fpga_config_file_dialog.show()

    def func_set_fpga_with_config_file_btn(self):
        log.debug("func func_set_fpga_with_config_file_btn clicked")
        self.get_fpga_config_json_file_dialog = None
        config_json_files_list = get_fpga_config_file_list(root_dir + '/fpga_config_jsons')
        self.get_fpga_config_json_file_dialog = GetFPGAConfigDialog(config_json_files_list)
        self.get_fpga_config_json_file_dialog.signal_fpga_config_json_get.connect(
            self.slot_get_fpga_config_json_file)
        self.get_fpga_config_json_file_dialog.show()

    def slot_gen_new_fpga_config_json_file(self, new_config_json_file_name: str):
        log.debug('slot_gen_new_fpga_config_json_file : %s', new_config_json_file_name)
        data = dict()
        data["fpga_config"] = []

        for fpga in self.fpga_list:
            params = {}
            for k, v in dataAddressDict.items():
                log.debug("read fpga id: %d, reg: %s", fpga.i_id, k)
                if 'gammaTable_' in k or 'test' in k:
                    pass
                elif k == 'gammaTable':
                    pass
                else:
                    ret, str_value = fpga.fpga_cmd_center.read_fpga_register(fpga.i_id, k)
                    if ret == 0:
                        params[k] = str_value
                    else:
                        params[k] = "unknown"
            data["fpga_config"].append(params)
            params = None

        with open(root_dir + '/fpga_config_jsons/' + new_config_json_file_name + ".json", "w") as json_file:
            json.dump(data, json_file, indent=2)
            log.debug('write json')

    def slot_get_fpga_config_json_file(self, config_json_file_name: str):
        log.debug("slot_get_fpga_config_json_file")
        fpga_setting_dict = load_fpga_json_file(config_json_file_name)
        target_fpga = None
        log.debug("len(fpga_setting_dict['fpga_config']): %d", len(fpga_setting_dict["fpga_config"]))
        # log.debug("fpga_setting_dict['fpga_config'][0] : %s", fpga_setting_dict['fpga_config'][0])
        for target_fpga_config_dict in fpga_setting_dict['fpga_config']:
            target_fpga = None
            for reg_name, reg_value in target_fpga_config_dict.items():
                if reg_name == "deviceID":
                    i_fpga_id = int(reg_value)
                    for tmp_fpga in self.fpga_list:
                        if tmp_fpga.i_id == i_fpga_id:
                            target_fpga = tmp_fpga
                            log.debug("got target_fpga, target_fpga_id :%d", target_fpga.i_id)
                elif reg_name == 'flashControl' or reg_name == 'UTC' or reg_name == 'MD5':
                    log.debug("%s does not need to write", reg_name)
                else:
                    if target_fpga is None:
                        log.debug("no such fpga, please check")
                        log.debug("popup a warning dialog")
                    else:
                        target_fpga.write_cmd(reg_name, str(reg_value))

            # log.debug("reg_name: %s,reg_value: %s ", reg_name, reg_value)

    def sync_clients_table(self, fpga_list: []):
        if len(fpga_list) == 0:
            log.debug("no fpga")
            return
        log.debug("sync_clients_table")
        self.fpga_list = fpga_list
        row_count = self.client_table_widget.rowCount()
        for i in reversed(range(row_count)):
            row_to_remove = self.client_table_widget.rowAt(i)
            self.client_table_widget.removeRow(row_to_remove)

        for fpga in self.fpga_list:
            row_count = self.client_table_widget.rowCount()
            self.client_table_widget.insertRow(row_count)
            self.client_table_widget.setItem(row_count, 0, QTableWidgetItem(str(fpga.i_id)))
            self.client_table_widget.setItem(row_count, 1, QTableWidgetItem(fpga.s_version))
            self.client_table_widget.setItem(row_count, 2, QTableWidgetItem(fpga.s_status))
            self.client_table_widget.setItem(row_count, 3, QTableWidgetItem(fpga.s_controls))

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
        log.debug("flash read write frame res test count : %d", self.frame_res_test_count)
        self.frame_res_test_count += 1
        flash_write_count_list = []
        flash_write_ok_list = [0, 0]
        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            ret, write_flash_count = self.fpga_list[i].read_cmd("flashWriteCount")
            if ret != 0:
                log.debug("read write_flash_count failed!")
                return
            else:
                log.debug("id : %d,write_flash_count : %d", i, write_flash_count)
            flash_write_count_list.append(write_flash_count)
        # time.sleep(2)
        self.main_windows.fpga_cmd_center.set_fpga_write_flash()
        time.sleep(5)
        while True:
            for i in range(len(self.fpga_list)):  # send cmd to id 2/3
                ret, write_flash_count = self.fpga_list[i].read_cmd("flashWriteCount")
                if ret != 0:
                    log.debug("read write_flash_count failed!")
                else:
                    log.debug("id : %d,write_flash_count : %d", i, write_flash_count)
                    if flash_write_count_list[i] < 255:
                        if write_flash_count != flash_write_count_list[i] + 1:
                            log.error("id: %d,write_flash_count did not add", i)
                        else:
                            log.debug("id : %d,write_flash_count add ok", i)
                            flash_write_ok_list[i] = 1
                    else:
                        if write_flash_count != 0:
                            log.error("id: %d,write_flash_count did not add", i)
                        else:
                            log.debug("id : %d,write_flash_count add ok", i)
                            flash_write_ok_list[i] = 1
            if flash_write_ok_list[0] == 1 and flash_write_ok_list[1] == 1:
                break
            time.sleep(1)

        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            ret, id_width = self.fpga_list[i].read_cmd("frameWidth")
            if ret == 0:
                if int(id_width) != 160:
                    log.fatal("id: %d, read frame width : %s, not match test frame width",
                              self.fpga_list[i].i_id, id_width)
            ret, id_height = self.fpga_list[i].read_cmd("frameHeight")
            if ret == 0:
                if int(id_height) != 48:
                    log.debug("id: %d, id_height: %s", self.fpga_list[i].i_id, id_height)
                    log.fatal("id: %d, read frame height : %s, not match test frame height",
                              self.fpga_list[i].i_id, id_width)

            '''ret, write_flash_count = self.fpga_list[i].read_cmd("flashWriteCount")
            if ret != 0:
                log.debug("read write_flash_count failed!")
            else:
                log.debug("id : %d,write_flash_count : %d", i, write_flash_count)

                if write_flash_count != flash_write_count_list[i] + 1:
                    log.error("id: %d,write_flash_count did not add", i)
                else:
                    log.debug("id : %d,write_flash_count add ok", i)'''

    def fpga_read_flash_test(self):
        log.debug("flash read write frame res test count : %d", self.frame_res_test_count)
        self.frame_res_test_count += 1
        flash_read_count_list = []
        flash_read_ok_list = [0, 0]
        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            ret, read_flash_count = self.fpga_list[i].read_cmd("flashReadCount")
            if ret != 0:
                log.debug("read read_flash_count failed!")
                return
            else:
                log.debug("id : %d,read_flash_count : %d", i, read_flash_count)
            flash_read_count_list.append(read_flash_count)
        # time.sleep(2)
        self.main_windows.fpga_cmd_center.set_fpga_read_flash()
        time.sleep(5)
        while True:
            for i in range(len(self.fpga_list)):  # send cmd to id 2/3
                ret, read_flash_count = self.fpga_list[i].read_cmd("flashReadCount")
                if ret != 0:
                    log.debug("read read_flash_count failed!")
                else:
                    log.debug("id : %d,read_flash_count : %d", i, read_flash_count)
                    if flash_read_count_list[i] < 255:
                        if read_flash_count != flash_read_count_list[i] + 1:
                            log.error("id: %d,read_flash_count did not add", i)
                        else:
                            log.debug("id : %d,read_flash_count add ok", i)
                            flash_read_ok_list[i] = 1
                    else:
                        if read_flash_count != 0:
                            log.error("id: %d,read_flash_count did not add", i)
                        else:
                            log.debug("id : %d,read_flash_count add ok", i)
                            flash_read_ok_list[i] = 1
            if flash_read_ok_list[0] == 1 and flash_read_ok_list[1] == 1:
                break

        for i in range(len(self.fpga_list)):  # send cmd to id 2/3
            ret, id_width = self.fpga_list[i].read_cmd("frameWidth")
            if ret == 0:
                if int(id_width) != 160:
                    log.fatal("id: %d, read frame width : %s, not match test frame width",
                              self.fpga_list[i].i_id, id_width)
            ret, id_height = self.fpga_list[i].read_cmd("frameHeight")
            if ret == 0:
                if int(id_height) != 48:
                    log.debug("id: %d, id_height: %s", self.fpga_list[i].i_id, id_height)
                    log.fatal("id: %d, read frame height : %s, not match test frame height",
                              self.fpga_list[i].i_id, id_width)

    def clients_menu_context_tree(self, position):
        log.debug("clients_menu_context_tree")
        q_table_widget_item = self.client_table_widget.itemAt(position)
        if q_table_widget_item is None:
            return
        log.debug("client ip :%s", q_table_widget_item.text())
        for fpga in self.fpga_list:
            if fpga.i_id == int(q_table_widget_item.text()):
                self.right_click_select_fpga = fpga

        pop_menu = QMenu()
        set_qstyle_dark(pop_menu)
        show_register_map_act = QAction("show_register_map", self)
        pop_menu.addAction(show_register_map_act)
        pop_menu.addSeparator()
        fpga_ota_act = QAction("OTA", self)
        pop_menu.addAction(fpga_ota_act)
        pop_menu.triggered[QAction].connect(self.client_page_pop_menu_trigger_act)

        pop_menu.exec_(self.client_table_widget.mapToGlobal(position))

    def slot_process_fpga_ota(self, ota_file: str):
        log.debug("start slot_process_fpga_ota, ota_file : %s", ota_file)
        target_ota_fpga = self.right_click_select_fpga
        log.debug("fpga id: %d going to OTA", target_ota_fpga.i_id)
        ota_file_size = os.path.getsize(ota_file)
        data_add_len = 0  # 2 byte
        data_len_per_packet = 1400
        log.debug("ota_file_size: %d", ota_file_size)
        with open(ota_file, 'rb') as f:
            for i in range(0, ota_file_size, data_len_per_packet):
                log.debug("i: %x", i)
                if (i + data_len_per_packet) > ota_file_size:
                    log.debug("The last shot, i: %d", i)
                    dataLen = ota_file_size - i
                    b_data = f.read(ota_file_size - i)
                    # data = data[::-1]    # LSB
                    # print("b_data:", b_data)
                    data_add_len = data_add_len - dataLen + len(b_data)
                    b_total_data = data_add_len.to_bytes(4, 'little') + b_data
                    i_ret = target_ota_fpga.fpga_cmd_center.process_fpga_ota(target_ota_fpga.i_id, b_total_data)
                    log.debug("send ota data i_ret: %d", i_ret)
                    if i_ret != 0:
                        log.debug("OTA Data Failed")
                        return
                    i_ret = target_ota_fpga.fpga_cmd_center.process_fpga_ota_finish(target_ota_fpga.i_id)

                    if i_ret != 0:
                        log.debug("OTA Finish Cmd Failed")
                        return
                    else:
                        log.debug("OTA Finish Cmd ")
                    break
                b_data = f.read(data_len_per_packet)
                b_total_data = data_add_len.to_bytes(4, 'little') + b_data
                i_ret = target_ota_fpga.fpga_cmd_center.process_fpga_ota(target_ota_fpga.i_id, b_total_data)
                if i_ret != 0:
                    log.debug("OTA Data Failed")
                    return
                data_add_len += data_len_per_packet

    def client_page_pop_menu_trigger_act(self, q):
        log.debug("%s", q.text())
        if q.text() == "show_register_map":
            if len(self.show_register_window) == 0:
                show_register_window = FPGARegWindow(self.right_click_select_fpga)
                show_register_window.show()
                self.show_register_window.append(show_register_window)
            else:
                for test_window in self.show_register_window:
                    if test_window.fpga == self.right_click_select_fpga:
                        test_window.show()
                    else:
                        show_register_window = FPGARegWindow(self.right_click_select_fpga)
                        show_register_window.show()
                        self.show_register_window.append(show_register_window)
        elif q.text() == "OTA":
            # target_ota_fpga = self.right_click_select_fpga
            # log.debug("fpga id: %d going to OTA", target_ota_fpga.i_id)
            self.select_fpga_ota_file_dialog = None
            fpga_ota_files_list = get_fpga_ota_file_list(root_dir + '/fpga_ota_files')
            self.select_fpga_ota_file_dialog = GetFPGAOTADialog(fpga_ota_files_list)
            self.select_fpga_ota_file_dialog.signal_fpga_ota_file_get.connect(
                self.slot_process_fpga_ota)
            self.select_fpga_ota_file_dialog.show()

    def video_params_changed(self):
        self.red_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_red_gain()))
        self.green_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_green_gain()))
        self.blue_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_blue_gain()))
        self.rgb_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))
        self.frame_width_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_width()))
        self.frame_height_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_height()))

    def show_info_message_box(self, win_title: str, info_text: str, pos_x=800, pos_y=600):
        try:
            info_dialog = QMessageBox(self)
            info_dialog.setIcon(QMessageBox.Information)
            info_dialog.setWindowTitle(win_title)
            info_dialog.setText(info_text)
            info_dialog.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
            info_dialog.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + "QPushButton {font-size:36px;}")
            info_dialog.move(pos_x, pos_y)
            info_dialog.show()
        except Exception as e:
            log.debug(e)