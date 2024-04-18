import qdarkstyle
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QGridLayout, QFrame, QLabel, QTextEdit, QPushButton
from global_def import log

class GenFPGAConfigJsonDialog(QWidget):
    signal_new_config_json_generate = pyqtSignal(str)

    def __init__(self, config_files_exists: list):

        super(GenFPGAConfigJsonDialog, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                      """
                      QMenu{
                          button-layout : 2;
                          font: bold 16pt "Brutal Type";
                          border: 3px solid #FFA042;
                          border-radius: 8px;
                          }
                      """)
        self.setWindowTitle("New FPGA Config Json File")

        self.layout = None
        self.new_config_file_lable = None
        self.new_config_file_textedit = None
        self.confirm_btn = None
        self.cancel_btn = None

        self.init_ui()
        self.config_files_exists = config_files_exists
        self.error_message_box = QMessageBox()

        self.error_message_box.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def init_ui(self):
        self.setFixedSize(400, 100)
        ''' Total frame layout'''
        self.layout = QGridLayout(self)
        layoutwidget = QFrame()
        layoutgridbox = QGridLayout()
        layoutwidget.setLayout(layoutgridbox)
        self.new_config_file_lable = QLabel()
        self.new_config_file_lable.setText("New Config Json Name")
        self.new_config_file_textedit = QTextEdit()
        self.new_config_file_textedit.setText("")
        self.new_config_file_textedit.setFixedHeight(40)

        self.confirm_btn = QPushButton()
        self.confirm_btn.setText("Ok")
        self.confirm_btn.setFixedWidth(80)
        self.confirm_btn.setFixedHeight(40)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setText("Cancel")
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setFixedHeight(40)
        layoutgridbox.addWidget(self.new_config_file_lable, 0, 1)
        layoutgridbox.addWidget(self.new_config_file_textedit, 1, 1)
        layoutgridbox.addWidget(self.cancel_btn, 1, 2)
        layoutgridbox.addWidget(self.confirm_btn, 1, 3)

        self.layout.addWidget(layoutwidget)

        self.confirm_btn.clicked.connect(self.confirm_btn_clicked)
        self.cancel_btn.clicked.connect(self.cancel_btn_clicked)

    def confirm_btn_clicked(self):
        log.debug("")
        if len(self.new_config_file_textedit.toPlainText()) == 0:
            self.show_error_message_box("Config Json Name Cannot be None")
            return

        config_file_name = self.new_config_file_textedit.toPlainText() + ".json"

        for pl in self.config_files_exists:
            if pl == config_file_name:
                self.show_error_message_box("Config json Name Already Exists")
                return

        self.signal_new_config_json_generate.emit(self.new_config_file_textedit.toPlainText())
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
