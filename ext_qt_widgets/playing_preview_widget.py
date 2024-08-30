from tokenize import Ignore

import qdarkstyle
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QFrame, QVBoxLayout, QSizePolicy
import time

from global_def import log
from qt_ui_style.button_qss import QFont_Style_Default, QFont_Style_Size_M
from utils.utils_file_access import get_led_config_from_file_uri, get_int_led_config_from_file_uri


class PlayingPreviewWindow(QWidget):

    def __init__(self, preview_width, preview_height):
        super(PlayingPreviewWindow, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                           """
                      QMenu{
                          button-layout : 2;
                          font: bold 16pt "Brutal Type";
                          border: 3px solid #FFA042;
                          border-radius: 8px;
                          }
                      """)
        self.setWindowTitle("Playing Preview")
        self.layout = None
        self.preview_info_label = None
        self.preview_label = None
        self.live_icon_label = None
        self.live_icon_pixmap = QPixmap("materials/live_icon.png").scaledToWidth(48)
        # self.image_display_width, self.image_display_height = (
        #    get_int_led_config_from_file_uri("led_wall_resolution", "led_wall_width", "led_wall_height"))
        self.image_display_width = preview_width
        self.image_display_height = preview_height
        self.init_ui()

        # self.error_message_box.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def init_ui(self):
        # self.setFixedSize(self.image_display_width, self.image_display_height)
        ''' Total frame layout'''
        self.layout = QGridLayout(self)
        layout_widget = QFrame()
        layout_gridbox = QGridLayout()
        # layout_vertical = QVBoxLayout()
        layout_widget.setLayout(layout_gridbox)
        self.preview_label = QLabel()
        self.preview_label.setText("Playing Preview")
        self.preview_info_label = QLabel()
        self.preview_info_label.setText("Res:WidthxHeight")
        self.preview_info_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.live_icon_label = QLabel()
        self.live_icon_label.setPixmap(self.live_icon_pixmap)

        # layout_gridbox.addWidget(self.preview_label, 1, 0, 10, 10)
        # layout_gridbox.addWidget(self.live_icon_label, 0, 0)
        self.preview_label.setScaledContents(True)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout_gridbox.addWidget(self.live_icon_label, 0, 0)
        layout_gridbox.addWidget(self.preview_info_label, 0, 1)
        layout_gridbox.addWidget(self.preview_label, 1, 0, 1, 2)
        self.layout.addWidget(layout_widget)

    def refresh_image(self, np_image):
        # log.debug("")
        qt_img = self.convert_ffmpeg_qt(np_image)
        if self.preview_label.width() != self.image_display_width or self.preview_label.height() != self.image_display_height:
            self.preview_label.setFixedSize(self.image_display_width,self.image_display_height)
            self.preview_info_label.setText("Res:{}x{}".format(self.image_display_width, self.image_display_height))
        # self.preview_label.setFixedWidth(qt_img.width())
        self.preview_label.setPixmap(qt_img)

    def convert_ffmpeg_qt(self, ffmpeg_img):
        """Convert from an opencv image to QPixmap"""
        # rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        # log.debug("%s", time.time())
        h, w, ch = ffmpeg_img.shape
        # log.debug("h: %d, w: %d, ch : %d", h, w, ch)
        # log.debug("self.image_display_width: %d, self.image_display_height: %d, ",
        #           self.image_display_width, self.image_display_height)
        bytes_per_line = ch * w
        self.image_display_width = w
        self.image_display_height = h
        convert_to_Qt_format = QImage(ffmpeg_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.image_display_width, self.image_display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(convert_to_Qt_format)
        # return QPixmap.fromImage(convert_to_Qt_format)

    def set_visible(self, is_visible: bool):
        log.debug("")
        self.setVisible(is_visible)

    def close_window(self):
        QTimer.singleShot(1000, self.perform_close)

    def perform_close(self):
        super().close()

