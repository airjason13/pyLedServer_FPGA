import hashlib
import os
import platform
import shutil

import qdarkstyle
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QMouseEvent, QMovie, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, \
    QAbstractItemView, QTreeWidgetItem, QLabel, QFrame, QMenu, QAction, QGridLayout, QPushButton, QLineEdit, QComboBox

from astral_hashmap import City_Map
from media_engine.media_engine import MediaEngine
from media_engine.media_engine_def import PlayStatus
from qt_ui_style.button_qss import QPushFileStopButton_Style, QPushFilePlayButton_Style, QFont_Style_Default, \
    QFont_Style_Size_M
from utils.utils_file_access import get_playlist_file_list, get_mount_points
from ext_qt_widgets.media_file_list import MediaFileList
from ext_qt_widgets.media_playlist import PlayList
from ext_qt_widgets.new_playlist_dialog_widget import NewPlaylistDialog
from ext_qt_widgets.system_file_watcher import FileWatcher
from global_def import log, MIN_FRAME_BRIGHTNESS, MAX_FRAME_BRIGHTNESS, MIN_FRAME_GAMMA, MAX_FRAME_GAMMA, \
    frame_brightness_alog, sleep_mode, icled_type
from ext_qt_widgets.custom_tree_widget import CTreeWidget
from media_configs.media_path_configs import *
from utils.gen_thumbnails import gen_webp_from_video_threading


class CMSPage(QWidget):
    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, **kwargs):
        super(CMSPage, self).__init__()
        self.main_windows = _main_window
        self.frame = _frame
        self.media_engine = media_engine
        self.widget = QWidget(self.frame)
        self.name = _name
        self.name_label = None
        self.layout = None
        self.init_ui()
        log.debug("CMS Page")


    def init_ui(self):
        self.name_label = QLabel(self.widget)
        self.name_label.setText(self.name)
        self.layout = QGridLayout()
        self.layout.addWidget(self.name_label, 1, 1)
        self.setLayout(self.layout)

