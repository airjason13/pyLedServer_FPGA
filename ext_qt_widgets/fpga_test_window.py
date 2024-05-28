import qdarkstyle
from PyQt5 import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QTableWidget, QAbstractScrollArea, QGridLayout, \
    QTableWidgetItem, QLineEdit, QPushButton, QHBoxLayout

from fpga.fpga_clients import FPGAClient
from qt_ui_style.button_qss import QFont_Style_Default, QFont_Style_Size_L, QFont_Style_Size_M
from global_def import log

common_reg_list = [
                    "currentGammaTable",
                    "frameWidth",
                    "frameHeight",
                    "currentGain",
                    "panelWay",
                    "ledArrangement",
                    "stringVersion",
                    "otaUpdateCount",
                    "ignoreLostFrame",
]

gamma_reg_list = []
for i in range(64):
    gamma_reg_list.append("gammaTable_r{}".format(str(i)))
    gamma_reg_list.append("gammaTable_g{}".format(str(i)))
    gamma_reg_list.append("gammaTable_b{}".format(str(i)))


layout_reg_list = []
for i in range(64):
    layout_reg_list.append("numberOfPixel_p{}".format(str(i)))
    layout_reg_list.append("startX_p{}".format(str(i)))
    layout_reg_list.append("startY_p{}".format(str(i)))
    layout_reg_list.append("portWidth_p{}".format(str(i)))
    layout_reg_list.append("portHeight_p{}".format(str(i)))


class FPGARegWindow(QWidget):
    def __init__(self, fpga: FPGAClient ):
        super(FPGARegWindow, self).__init__()
        self.resize(960, 1080)
        self.setWindowOpacity(1.0)  # 窗口透明度
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.fpga = fpga
        # Label
        self.main_widget = QWidget(self)
        self.info_widget = QWidget()
        self.info_widget_layout = QHBoxLayout()
        self.info_label = QLabel()
        self.refresh_btn = QPushButton()
        self.register_map_table_widget = QWidget()
        self.common_register_map_table = QTableWidget()
        self.gamma_register_map_table = QTableWidget()
        self.layout_register_map_table = QTableWidget()
        self.register_layout = QGridLayout()
        self.cmd_widget = QWidget()
        self.cmd_widget_layout = QGridLayout()
        self.r_gain_label = QLabel()
        self.r_gain_lineedit = QLineEdit()
        self.g_gain_label = QLabel()
        self.g_gain_lineedit = QLineEdit()
        self.b_gain_label = QLabel()
        self.b_gain_lineedit = QLineEdit()
        self.set_current_gain_btn = QPushButton()
        self.main_layout = QVBoxLayout()

        self.init_ui()
        self.refresh_status = True

        self.refresh_common_reg_table()
        self.refresh_gamma_reg_table()
        self.refresh_layout_reg_table()
        self.refresh_status = False

        self.common_register_map_table.cellChanged.connect(self.common_register_map_table_cell_changed)
        self.layout_register_map_table.cellChanged.connect(self.layout_register_map_table_cell_changed)

    def init_ui(self):
        self.info_label.setText('FPGA {} Info'.format(str(self.fpga.i_id)))
        self.info_label.setStyleSheet('font-size:40px')

        self.refresh_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.refresh_btn.setText("Refresh Reg")
        self.refresh_btn.clicked.connect(self.func_refresh_btn)

        self.info_widget_layout.addWidget(self.info_label)
        self.info_widget_layout.addWidget(self.refresh_btn)
        self.info_widget.setLayout(self.info_widget_layout)

        self.common_register_map_table.setColumnCount(2)
        self.common_register_map_table.setFixedSize(320, 280)
        self.common_register_map_table.setColumnWidth(0, 180)
        self.common_register_map_table.setColumnWidth(1, 120)
        self.common_register_map_table.setRowCount(0)
        self.common_register_map_table.horizontalHeader().setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.common_register_map_table.horizontalHeader().setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.common_register_map_table.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.common_register_map_table.setHorizontalHeaderLabels(['Common Register', 'Value'])

        self.gamma_register_map_table.setColumnCount(2)
        self.gamma_register_map_table.setRowCount(0)
        self.gamma_register_map_table.setColumnWidth(0, 180)
        self.gamma_register_map_table.setColumnWidth(1, 120)
        self.gamma_register_map_table.horizontalHeader().setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.gamma_register_map_table.horizontalHeader().setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.gamma_register_map_table.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.gamma_register_map_table.setHorizontalHeaderLabels(['Gamma Register', 'Value'])

        self.layout_register_map_table.setColumnCount(2)
        self.layout_register_map_table.setFixedSize(360, 720)
        self.layout_register_map_table.setColumnWidth(0, 180)
        self.layout_register_map_table.setColumnWidth(1, 160)
        self.layout_register_map_table.setRowCount(0)
        self.layout_register_map_table.horizontalHeader().setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.layout_register_map_table.horizontalHeader().setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.layout_register_map_table.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.layout_register_map_table.setHorizontalHeaderLabels(['Layout Register', 'Value'])

        self.register_layout.addWidget(self.common_register_map_table, 0, 0)
        self.register_layout.addWidget(self.gamma_register_map_table, 1, 0)
        self.register_layout.addWidget(self.layout_register_map_table, 0, 1, 2, 2)
        self.register_map_table_widget.setLayout(self.register_layout)

        self.r_gain_label.setText("RGain:")
        self.g_gain_label.setText("GGain:")
        self.b_gain_label.setText("BGain:")
        self.set_current_gain_btn.setText("Set")
        self.set_current_gain_btn.clicked.connect(self.set_current_gain_btn_clicked)

        self.cmd_widget_layout.addWidget(self.r_gain_label, 0, 0)
        self.cmd_widget_layout.addWidget(self.r_gain_lineedit, 0, 1)
        self.cmd_widget_layout.addWidget(self.g_gain_label, 0, 2)
        self.cmd_widget_layout.addWidget(self.g_gain_lineedit, 0, 3)
        self.cmd_widget_layout.addWidget(self.b_gain_label, 0, 4)
        self.cmd_widget_layout.addWidget(self.b_gain_lineedit, 0, 5)
        self.cmd_widget_layout.addWidget(self.set_current_gain_btn, 0, 6)
        self.cmd_widget.setLayout(self.cmd_widget_layout)

        self.main_layout.addWidget(self.info_widget)
        # self.main_layout.addWidget(self.refresh_btn)
        self.main_layout.addWidget(self.register_map_table_widget)
        self.main_layout.addWidget(self.cmd_widget)
        self.main_widget.setLayout(self.main_layout)

    def func_refresh_btn(self):
        log.debug("func_refresh_btn")
        self.refresh_status = True

        self.refresh_common_reg_table()
        self.refresh_gamma_reg_table()
        self.refresh_layout_reg_table()
        self.refresh_status = False

    def refresh_common_reg_table(self):
        row_count = self.common_register_map_table.rowCount()
        for i in reversed(range(self.common_register_map_table.rowCount())):
            row_to_remove = self.common_register_map_table.rowAt(i)
            self.common_register_map_table.removeRow(row_to_remove)

        for reg in common_reg_list:
            row_count = self.common_register_map_table.rowCount()
            self.common_register_map_table.insertRow(row_count)
            self.common_register_map_table.setItem(row_count, 0, QTableWidgetItem(reg))
            if reg == 'stringVersion':
                ret, reg_value = self.fpga.fpga_cmd_center.read_fpga_register_bytes(self.fpga.i_id, reg)
            else:
                ret, reg_value = self.fpga.fpga_cmd_center.read_fpga_register(self.fpga.i_id, reg)
            if ret == 0:
                if reg == "currentGain":
                    self.common_register_map_table.setItem(row_count, 1, QTableWidgetItem(hex(reg_value)))
                elif reg == "stringVersion":
                    self.common_register_map_table.setItem(row_count, 1, QTableWidgetItem(reg_value.decode()))
                else:
                    self.common_register_map_table.setItem(row_count, 1, QTableWidgetItem(str(reg_value)))
            else:
                self.common_register_map_table.setItem(row_count, 1, QTableWidgetItem("unknown"))

    def refresh_gamma_reg_table(self):
        current_gamma_index = -1
        row_count = self.common_register_map_table.rowCount()
        for i in range(row_count):
            if self.common_register_map_table.item(i, 0).text() == common_reg_list[0]:
                current_gamma_index = int(self.common_register_map_table.item(i, 1).text())
        if current_gamma_index == -1:
            log.debug("current_gamma_index error! value : %d", current_gamma_index)
            return

        log.debug("curren_gamma_index : %d", current_gamma_index)

        for gamma_register_index in reversed(range(self.gamma_register_map_table.rowCount())):
            row_to_remove = self.gamma_register_map_table.rowAt(gamma_register_index)
            self.gamma_register_map_table.removeRow(row_to_remove)

        if current_gamma_index == 0:
            target_gamma_table_list = [
                "gammaTable_r{}".format(str(current_gamma_index)),
                "gammaTable_g{}".format(str(current_gamma_index)),
                "gammaTable_b{}".format(str(current_gamma_index))
            ]
        else:
            target_gamma_table_list = [
                "gammaTable_r{}".format(str(current_gamma_index-1)),
                "gammaTable_g{}".format(str(current_gamma_index-1)),
                "gammaTable_b{}".format(str(current_gamma_index-1)),
                "gammaTable_r{}".format(str(current_gamma_index)),
                "gammaTable_g{}".format(str(current_gamma_index)),
                "gammaTable_b{}".format(str(current_gamma_index))
            ]

        for reg in target_gamma_table_list:
            row_count = self.gamma_register_map_table.rowCount()
            self.gamma_register_map_table.insertRow(row_count)
            self.gamma_register_map_table.setItem(row_count, 0, QTableWidgetItem(reg))
            # ret, reg_value = self.fpga.fpga_cmd_center.read_fpga_register(self.fpga.i_id, reg)

            ret, reg_value_bytes = self.fpga.fpga_cmd_center.read_fpga_register_bytes(self.fpga.i_id, reg)

            if ret == 0:
                # log.debug("%s : %s", reg, str(reg_value))
                self.gamma_register_map_table.setItem(row_count, 1, QTableWidgetItem(str(reg_value_bytes)))
            else:
                self.gamma_register_map_table.setItem(row_count, 1, QTableWidgetItem("unknown"))

    def refresh_layout_reg_table(self):
        row_count = self.layout_register_map_table.rowCount()
        log.debug("row_count : %s", row_count)
        for i in reversed(range(self.layout_register_map_table.rowCount())):
            row_to_remove = self.layout_register_map_table.rowAt(i)
            self.layout_register_map_table.removeRow(row_to_remove)
        log.debug("self.layout_register_map_table.rowCount() : %s", self.layout_register_map_table.rowCount())
        for reg in layout_reg_list:
            row_count = self.layout_register_map_table.rowCount()
            self.layout_register_map_table.insertRow(row_count)
            self.layout_register_map_table.setItem(row_count, 0, QTableWidgetItem(reg))
            ret, reg_value = self.fpga.fpga_cmd_center.read_fpga_register(self.fpga.i_id, reg)
            if ret == 0:
                self.layout_register_map_table.setItem(row_count, 1, QTableWidgetItem(str(reg_value)))
            else:
                self.layout_register_map_table.setItem(row_count, 1, QTableWidgetItem("unknown"))

    def set_current_gain_btn_clicked(self):
        log.debug("set_current_gain_btn_clicked")
        i_current_gain_value = -1
        if (self.r_gain_lineedit.text() is None or
                self.g_gain_lineedit.text() is None or
                self.r_gain_lineedit.text() is None):
            log.debug("value is empty!")
            return
        else:
            i_r_gain_value = int(self.r_gain_lineedit.text())
            i_g_gain_value = int(self.g_gain_lineedit.text())
            i_b_gain_value = int(self.b_gain_lineedit.text())
            i_current_gain_value = i_r_gain_value << 16 | i_g_gain_value << 8 | i_b_gain_value
        if i_current_gain_value == -1:
            log.debug("i_current_gain_value is still initial value")
            return
        log.debug("i_current_gain_value = %d", i_current_gain_value)
        self.refresh_status = True
        # set current gain
        self.fpga.fpga_cmd_center.write_fpga_register(self.fpga.i_id, "currentGain",
                                                      str(i_current_gain_value))

        self.refresh_common_reg_table()
        self.refresh_status = False

    def layout_register_map_table_cell_changed(self, row, column):
        if self.refresh_status is True:
            return
        log.debug("layout_register_map_table_cell_changed row : %d, column : %d", row, column)
        reg_name = self.layout_register_map_table.item(row, 0).text()
        target_reg_value = self.layout_register_map_table.item(row, column).text()
        log.debug("fpga_id: %d, reg_name : %s, target_reg_value : %s", self.fpga.i_id, reg_name, target_reg_value)
        self.fpga.fpga_cmd_center.write_fpga_register(self.fpga.i_id, reg_name,
                                                      target_reg_value)

    def common_register_map_table_cell_changed(self, row, column):
        if self.refresh_status is True:
            return
        log.debug("common_register_map_table_cell_changed row : %d, column : %d", row, column)
        reg_name = self.common_register_map_table.item(row, 0).text()
        target_reg_value = self.common_register_map_table.item(row, column).text()
        if reg_name == "CurrentGain":
            log.debug("Don't handle currentGain")
            return
        log.debug("fpga_id: %d, reg_name : %s, target_reg_value : %s", self.fpga.i_id, reg_name, target_reg_value)
        self.fpga.fpga_cmd_center.write_fpga_register(self.fpga.i_id, reg_name,
                                                      target_reg_value)




