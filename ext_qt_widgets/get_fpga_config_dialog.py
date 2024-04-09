import qdarkstyle
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QGridLayout, QFrame, QLabel, QTextEdit, QPushButton, QComboBox
from global_def import log


class GetFPGAConfigDialog(QWidget):
    signal_fpga_config_json_get = pyqtSignal(str)

    def __init__(self, config_files_exists: list):

        super(GetFPGAConfigDialog, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                           """
                      QMenu{
                          button-layout : 2;
                          font: bold 16pt "Brutal Type";
                          border: 3px solid #FFA042;
                          border-radius: 8px;
                          }
                      """)
        self.setWindowTitle("Choose FPGA Config Json File")

        self.config_files_exists = config_files_exists
        print("self.config_files_exists :", self.config_files_exists)
        self.select_fpga_config_file = None
        self.layout = None
        self.new_config_file_lable = None
        self.json_file_list_combobox = None
        self.confirm_btn = None
        self.cancel_btn = None

        self.init_ui()
        self.error_message_box = QMessageBox()
        self.error_message_box.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def init_ui(self):
        self.setFixedSize(400, 100)
        ''' Total frame layout'''
        self.layout = QGridLayout(self)
        layout_widget = QFrame()
        layout_gridbox = QGridLayout()
        layout_widget.setLayout(layout_gridbox)
        self.new_config_file_lable = QLabel()
        self.new_config_file_lable.setText("Choose Config Json File")
        self.json_file_list_combobox = QComboBox(self)
        if len(self.config_files_exists) == 0:
            self.json_file_list_combobox.addItems(['No Config Files'])
        else:
            self.json_file_list_combobox.addItems(self.config_files_exists)
        self.select_fpga_config_file = self.json_file_list_combobox.currentText()
        self.json_file_list_combobox.currentIndexChanged.connect(self.json_file_list_combobox_index_changed)

        self.confirm_btn = QPushButton()
        self.confirm_btn.setText("Ok")
        self.confirm_btn.setFixedWidth(80)
        self.confirm_btn.setFixedHeight(40)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setText("Cancel")
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setFixedHeight(40)
        layout_gridbox.addWidget(self.new_config_file_lable, 0, 1)
        layout_gridbox.addWidget(self.json_file_list_combobox, 1, 1)
        layout_gridbox.addWidget(self.cancel_btn, 1, 2)
        layout_gridbox.addWidget(self.confirm_btn, 1, 3)

        self.layout.addWidget(layout_widget)

        self.confirm_btn.clicked.connect(self.confirm_btn_clicked)
        self.cancel_btn.clicked.connect(self.cancel_btn_clicked)

    def json_file_list_combobox_index_changed(self):
        log.debug("json_file_list_combobox_index_changed")
        self.select_fpga_config_file = self.json_file_list_combobox.currentText()

    def confirm_btn_clicked(self):
        log.debug("select_fpga_config_file : %s", self.select_fpga_config_file)
        self.signal_fpga_config_json_get.emit(self.select_fpga_config_file)
        self.destroy()

    def cancel_btn_clicked(self):
        log.debug("")
        self.destroy()

    def show_error_message_box(self, error_str):
        if self.error_message_box is None:
            self.error_message_box = QMessageBox()
            self.error_message_box.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        self.error_message_box.hide()

        self.error_message_box.setIcon(QMessageBox.Critical)
        self.error_message_box.setText("Error")
        self.error_message_box.setInformativeText(error_str)
        self.error_message_box.setWindowTitle("Error")
        self.error_message_box.show()
