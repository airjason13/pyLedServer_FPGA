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


class MediaFilesPage(QWidget):
    File_List_Font_Size = 24
    Preview_Widget_Width = 320
    Preview_Widget_Height = 240
    TAG_Str_Media_Folder = '/media/'
    TAG_Str_Media_Files = 'Media Files'
    TAG_Str_Internal_Media = 'Internal Media'
    TAG_Str_External_Media = 'External Media'
    TAG_Str_Playlist = 'Playlist'

    TAG_Str_Popup_Menu_Play = 'Play'
    TAG_Str_Popup_Menu_Delete = 'Delete'
    TAG_Str_Popup_Menu_Play_Playlist = "Play Playlist"
    TAG_Str_Popup_Menu_Delete_Playlist = 'Delete Playlist'
    TAG_Str_Popup_Menu_Add_to = 'Add to '
    TAG_Str_Popup_Menu_Add_to_Playlist = 'Add to Playlist'
    TAG_Str_Popup_Menu_Add_to_New_Playlist = 'New Playlist'
    TAG_Str_Popup_Menu_Copy_To_Internal = 'Copy to Internal'
    TAG_Str_Popup_Menu_Remove_From_Playlist = 'Remove From Playlist'
    TAG_Str_Splash_Mark = "/"
    TAG_Str_Playlist_Extension = '.playlist'

    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, **kwargs):
        super(MediaFilesPage, self).__init__()
        self.media_active_height = 0
        self.media_active_width = 0
        self.video_params_setting_widget = None
        self.video_crop_x_lineedit = None
        self.video_crop_y_lineedit = None
        self.video_crop_w_lineedit = None
        self.video_crop_h_lineedit = None
        self.media_adj_crop_btn = None

        self.video_brightness_label = None
        self.video_gamma_label = None
        self.video_brightness_lineedit = None
        self.video_gamma_lineedit = None
        self.video_adj_br_ga_btn = None

        self.brightness_algo_label = None
        self.brightness_algo_combobox = None
        self.sleep_mode_enable_label = None
        self.sleep_mode_enable_combobox = None
        self.target_city_label = None
        self.target_city_combobox = None

        self.day_mode_brightness_label = None
        self.day_mode_brightness_lineedit = None
        self.night_mode_brightness_label = None
        self.night_mode_brightness_lineedit = None
        self.sleep_mode_brightness_label = None
        self.sleep_mode_brightness_lineedit = None

        self.icled_type_label = None
        self.icled_type_combobox = None

        self.led_r_gain_label = None
        self.led_r_gain_lineedit = None
        self.led_g_gain_label = None
        self.led_g_gain_lineedit = None
        self.led_b_gain_label = None
        self.led_b_gain_lineedit = None

        self.output_frame_width_label = None
        self.output_frame_width_lineedit = None
        self.output_frame_height_label = None
        self.output_frame_height_lineedit = None
        self.output_fps_label = None
        self.output_fps_lineedit = None

        self.video_params_setting_layout = None

        self.preview_control_btn = None
        self.sound_control_btn = None
        self.main_windows = _main_window
        self.frame = _frame
        self.media_engine = media_engine

        self.frame.setMouseTracking(True)
        self.widget = QWidget(self.frame)
        self.name = _name
        self.media_files_tree_widget = None
        self.layout = None

        ''' mouse right click position'''
        self.right_clicked_pos = None

        ''' 創建 Playlist 對話窗'''
        self.NewPlaylistDialog = None

        ''' 檔案預覽畫面縮圖 '''
        self.preview_file_name = None
        self.preview_file_movie = None
        self.internal_media_file_tree_widget_root = None
        self.external_media_file_tree_widget_root = None
        self.media_playlist_tree_widget_root = None

        ''' media file list internal '''
        self.internal_media_folder = []
        self.internal_media_folder.append(os.path.expanduser("~" + MediaFileFolder))
        self.media_file_list_internal = []
        for d in self.internal_media_folder:
            self.media_file_list_internal.append(MediaFileList(d))
        log.debug("mount point : %s", get_mount_points())
        self.external_media_folder = get_mount_points()
        self.media_file_list_external = []
        for d in self.external_media_folder:
            self.media_file_list_external.append(MediaFileList(d))

        '''handle the playlist'''
        self.playlist_files_list = get_playlist_file_list(self.internal_media_folder[0] + PlaylistFolder)
        log.debug("playlist_files_list : %s", self.playlist_files_list)
        self.media_playlist = []
        for file in self.playlist_files_list:
            playlist_tmp = PlayList(file)
            self.media_playlist.append(playlist_tmp)

        '''media control panel'''
        self.media_control_panel = None
        self.media_control_panel_layout = None

        '''button initial'''
        self.play_pause_btn = None
        self.play_stop_btn = None
        self.play_icon = None
        self.pause_icon = None
        self.stop_icon = None
        self.play_icon_pixmap = None
        self.pause_icon_pixmap = None
        self.stop_icon_pixmap = None
        self.select_current_file_uri = None
        self.init_ui()

        self.media_engine.install_signal_media_play_status_changed_slot(self.media_play_status_changed)

        media_preview_widget = QLabel()
        media_preview_widget.setFrameShape(QFrame.StyledPanel)
        media_preview_widget.setWindowFlags(Qt.ToolTip)
        media_preview_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        media_preview_widget.hide()
        self.media_preview_widget = media_preview_widget

        ''' install file watcher signal/slot'''
        self.internal_file_watcher = FileWatcher(self.internal_media_folder)
        self.internal_file_watcher.install_folder_changed_slot(self.internal_media_files_changed)

        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            '''Could not use os.login() for launch at start-up'''
            self.external_file_watcher = FileWatcher([self.TAG_Str_Media_Folder + 'root'])
            self.external_file_watcher.install_folder_changed_slot(self.external_media_files_changed)
        else:
            self.external_file_watcher = FileWatcher([self.TAG_Str_Media_Folder + os.getlogin()])
            self.external_file_watcher.install_folder_changed_slot(self.external_media_files_changed)

        # install media_engine.video_params video_params_changed slot
        self.media_engine.led_video_params.install_video_params_changed_slot(self.video_params_changed)

    def init_ui(self):
        self.media_files_tree_widget = CTreeWidget(self.frame)
        '''install media_files_tree_widget mouse qsignal/slot'''
        self.media_files_tree_widget.qsignal_mouse_move.connect(self.mouse_move_on_tree)
        font = QFont()
        font.setPointSize(self.File_List_Font_Size)
        self.media_files_tree_widget.setFont(font)
        self.media_files_tree_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.media_files_tree_widget.setColumnCount(1)
        self.media_files_tree_widget.setColumnWidth(0, 300)
        self.media_files_tree_widget.headerItem().setText(0, "Media Files")
        '''Enable mouse tracker on media_files_tree_widget'''
        self.media_files_tree_widget.setMouseTracking(True)
        '''Enable 右鍵選單 '''
        self.media_files_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.media_files_tree_widget.customContextMenuRequested.connect(self.right_click_context_menu)

        ''' Handle Internal Media Folder '''
        self.internal_media_file_tree_widget_root = QTreeWidgetItem(self.media_files_tree_widget)

        self.internal_media_file_tree_widget_root.setText(0, self.TAG_Str_Internal_Media)
        self.refresh_internal_media_file_list_tree_widget()

        ''' Handle External Media Folder '''
        self.external_media_file_tree_widget_root = QTreeWidgetItem(self.media_files_tree_widget)
        self.external_media_file_tree_widget_root.setText(0, self.TAG_Str_External_Media)
        self.refresh_external_media_file_list_tree_widget()

        ''' Handle Media Playlist '''
        self.media_playlist_tree_widget_root = QTreeWidgetItem(self.media_files_tree_widget)
        self.media_playlist_tree_widget_root.setText(0, self.TAG_Str_Playlist)
        self.refresh_media_playlist_tree_widget()

        self.media_files_tree_widget.addTopLevelItem(self.internal_media_file_tree_widget_root)
        self.media_files_tree_widget.addTopLevelItem(self.external_media_file_tree_widget_root)

        ''' Media Control Panel Initial'''
        self.media_control_panel = QWidget()
        self.media_control_panel_layout = QGridLayout()
        self.media_control_panel.setLayout(self.media_control_panel_layout)
        self.video_params_setting_widget = QWidget(self.media_control_panel)
        self.video_params_setting_layout = QGridLayout(self.video_params_setting_widget)

        ''' Handle Play/Pause/Stop/Preview/Sound Button'''
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(128, 128)
        self.play_icon_pixmap = QPixmap("materials/play_btn.png").scaledToWidth(128)
        self.play_icon = QIcon(self.play_icon_pixmap)
        self.pause_icon_pixmap = QPixmap("materials/pause_btn.png").scaledToWidth(128)
        self.pause_icon = QIcon(self.pause_icon_pixmap)
        self.play_pause_btn.setIcon(self.play_icon)
        self.play_pause_btn.setIconSize(QSize(128, 128))
        self.play_pause_btn.setStyleSheet(QPushFilePlayButton_Style)
        self.play_pause_btn.clicked.connect(self.pause_btn_clicked)
        self.media_control_panel_layout.addWidget(self.play_pause_btn, 0, 1)

        self.play_stop_btn = QPushButton()
        self.play_stop_btn.setFixedSize(128, 128)
        self.stop_icon_pixmap = QPixmap("materials/stop_btn.png").scaledToWidth(128)
        self.stop_icon = QIcon(self.stop_icon_pixmap)
        self.play_stop_btn.setIcon(self.stop_icon)
        self.play_stop_btn.setIconSize(QSize(128, 128))
        self.play_stop_btn.setStyleSheet(QPushFileStopButton_Style)
        self.play_stop_btn.clicked.connect(self.stop_btn_clicked)

        self.sound_control_btn = QPushButton()

        if self.media_engine.led_video_params.get_play_with_audio() == 1:
            self.sound_control_btn.setIcon(QIcon('materials/soundOnIcon.png'))
        else:
            self.sound_control_btn.setIcon(QIcon('materials/soundOffIcon.png'))

        self.sound_control_btn.setIconSize(QSize(32, 32))
        self.sound_control_btn.setCheckable(True)
        self.sound_control_btn.setChecked(not self.media_engine.led_video_params.get_play_with_audio())
        self.sound_control_btn.clicked.connect(self.sound_btn_clicked)

        self.preview_control_btn = QPushButton()

        if self.media_engine.led_video_params.get_play_with_preview() == 1:
            self.preview_control_btn.setIcon(QIcon('materials/eyeOpenIcon.png'))
        else:
            self.preview_control_btn.setIcon(QIcon('materials/eyeCloseIcon.png'))

        self.preview_control_btn.setIconSize(QSize(32, 32))
        self.preview_control_btn.setCheckable(True)
        self.preview_control_btn.setChecked(not self.media_engine.led_video_params.get_play_with_preview())
        self.preview_control_btn.clicked.connect(self.preview_btn_clicked)

        self.video_crop_x_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_crop_y_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_crop_w_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_crop_h_lineedit = QLineEdit(self.video_params_setting_widget)

        self.video_crop_x_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_x()))
        self.video_crop_y_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_y()))
        self.video_crop_w_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_w()))
        self.video_crop_h_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_h()))

        edits = [self.video_crop_x_lineedit, self.video_crop_y_lineedit, self.video_crop_w_lineedit,
                 self.video_crop_h_lineedit]

        labels = ["Crop Start X:", "Crop Start Y:", "Crop Width:", "Crop Height:"]
        for i, label in enumerate(labels):
            lbl = QLabel(label, self.video_params_setting_widget)
            lbl.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
            edit = edits[i]
            edit.setFixedWidth(100)
            edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
            self.video_params_setting_layout.addWidget(lbl, i, 0)
            self.video_params_setting_layout.addWidget(edit, i, 1)

        self.media_adj_crop_btn = QPushButton("Adjust Crop Parameter", self.video_params_setting_widget)
        self.media_adj_crop_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.media_adj_crop_btn.clicked.connect(self.adj_media_ctrl_param)

        ''' Brightness Setting '''
        self.video_brightness_label = QLabel(self.video_params_setting_widget)
        self.video_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_brightness_label.setText("Frame Brightness:")
        self.video_gamma_label = QLabel(self.video_params_setting_widget)
        self.video_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_gamma_label.setText("Frame Gamma:")

        self.video_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_brightness_lineedit.setFixedWidth(100)
        self.video_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_brightness_lineedit.setText(str(self.media_engine.led_video_params.get_led_brightness()))

        self.video_gamma_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_gamma_lineedit.setFixedWidth(100)
        self.video_gamma_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))

        self.brightness_algo_label = QLabel(self.video_params_setting_widget)
        self.brightness_algo_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.brightness_algo_label.setText("Brightness Method:")
        self.brightness_algo_combobox = QComboBox(self.video_params_setting_widget)
        self.brightness_algo_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for i in frame_brightness_alog:
            if '.' in str(i):
                self.brightness_algo_combobox.addItem(str(i).split(".")[1])
            else:
                self.brightness_algo_combobox.addItem(str(i))
        self.brightness_algo_combobox.setCurrentIndex(self.media_engine.led_video_params.get_frame_brightness_algo())

        self.sleep_mode_enable_label = QLabel(self.video_params_setting_widget)
        self.sleep_mode_enable_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.sleep_mode_enable_label.setText("Sleep Mode:")
        self.sleep_mode_enable_combobox = QComboBox(self.video_params_setting_widget)
        self.sleep_mode_enable_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for i in sleep_mode:
            if '.' in str(i):
                self.sleep_mode_enable_combobox.addItem(str(i).split(".")[1])
            else:
                self.sleep_mode_enable_combobox.addItem(str(i))
        self.sleep_mode_enable_combobox.setCurrentIndex(self.media_engine.led_video_params.get_sleep_mode_enable())

        self.target_city_label = QLabel(self.video_params_setting_widget)
        self.target_city_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.target_city_label.setText("City:")
        self.target_city_combobox = QComboBox(self.video_params_setting_widget)
        self.target_city_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for city in City_Map:
            self.target_city_combobox.addItem(city.get("City"))
        self.target_city_combobox.setCurrentIndex(int(self.media_engine.led_video_params.get_target_city_index()))

        self.day_mode_brightness_label = QLabel(self.video_params_setting_widget)
        self.day_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.day_mode_brightness_label.setText("Day Mode Brightness:")
        self.day_mode_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.day_mode_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.day_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_day_mode_frame_brightness()))

        self.night_mode_brightness_label = QLabel(self.video_params_setting_widget)
        self.night_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.night_mode_brightness_label.setText("Night Mode Brightness:")
        self.night_mode_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.night_mode_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.night_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_night_mode_frame_brightness()))

        self.sleep_mode_brightness_label = QLabel(self.video_params_setting_widget)
        self.sleep_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.sleep_mode_brightness_label.setText("Sleep Mode Brightness:")
        self.sleep_mode_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.sleep_mode_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.sleep_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_sleep_mode_frame_brightness()))

        self.led_r_gain_label = QLabel(self.video_params_setting_widget)
        self.led_r_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_r_gain_label.setText("Led R Gain:")
        self.led_r_gain_lineedit = QLineEdit(self.video_params_setting_widget)
        self.led_r_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_r_gain_lineedit.setText(
            str(self.media_engine.led_video_params.get_led_red_gain()))

        self.led_g_gain_label = QLabel(self.video_params_setting_widget)
        self.led_g_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_g_gain_label.setText("Led G Gain:")
        self.led_g_gain_lineedit = QLineEdit(self.video_params_setting_widget)
        self.led_g_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_g_gain_lineedit.setText(
            str(self.media_engine.led_video_params.get_led_green_gain()))

        self.led_b_gain_label = QLabel(self.video_params_setting_widget)
        self.led_b_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_b_gain_label.setText("Led G Gain:")
        self.led_b_gain_lineedit = QLineEdit(self.video_params_setting_widget)
        self.led_b_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_b_gain_lineedit.setText(
            str(self.media_engine.led_video_params.get_led_blue_gain()))

        self.icled_type_label = QLabel(self.video_params_setting_widget)
        self.icled_type_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.icled_type_label.setText("ICLed Type:")
        self.icled_type_combobox = QComboBox(self.video_params_setting_widget)
        self.icled_type_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for str_type in icled_type:
            if '.' in str(str_type):
                self.icled_type_combobox.addItem(str(str_type).split(".")[1])
            else:
                self.icled_type_combobox.addItem(str(str_type))
        self.icled_type_combobox.setCurrentIndex(int(self.media_engine.led_video_params.get_icled_type()))

        self.output_frame_width_label = QLabel(self.video_params_setting_widget)
        self.output_frame_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_width_label.setText("Frame Width:")
        self.output_frame_width_lineedit = QLineEdit(self.video_params_setting_widget)
        self.output_frame_width_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_width_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_width()))

        self.output_frame_height_label = QLabel(self.video_params_setting_widget)
        self.output_frame_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_height_label.setText("Frame Height:")
        self.output_frame_height_lineedit = QLineEdit(self.video_params_setting_widget)
        self.output_frame_height_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_height_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_height()))

        self.output_fps_label = QLabel(self.video_params_setting_widget)
        self.output_fps_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_fps_label.setText("FPS:")
        self.output_fps_lineedit = QLineEdit(self.video_params_setting_widget)
        self.output_fps_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_fps_lineedit.setText(str(self.media_engine.led_video_params.get_output_fps()))

        self.video_adj_br_ga_btn = QPushButton("Adjust Brightness Parameter", self.video_params_setting_widget)
        self.video_adj_br_ga_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_adj_br_ga_btn.clicked.connect(self.adj_video_br_ga_param)

        self.video_params_setting_layout.addWidget(self.video_brightness_label, 0, 2)
        self.video_params_setting_layout.addWidget(self.video_gamma_label, 1, 2)
        self.video_params_setting_layout.addWidget(self.video_brightness_lineedit, 0, 3)
        self.video_params_setting_layout.addWidget(self.video_gamma_lineedit, 1, 3)
        self.video_params_setting_layout.addWidget(self.brightness_algo_label, 2, 2)
        self.video_params_setting_layout.addWidget(self.brightness_algo_combobox, 2, 3)
        self.video_params_setting_layout.addWidget(self.target_city_label, 3, 2)
        self.video_params_setting_layout.addWidget(self.target_city_combobox, 3, 3)

        self.video_params_setting_layout.addWidget(self.sleep_mode_enable_label, 0, 4)
        self.video_params_setting_layout.addWidget(self.sleep_mode_enable_combobox, 0, 5)
        self.video_params_setting_layout.addWidget(self.day_mode_brightness_label, 1, 4)
        self.video_params_setting_layout.addWidget(self.day_mode_brightness_lineedit, 1, 5)
        self.video_params_setting_layout.addWidget(self.night_mode_brightness_label, 2, 4)
        self.video_params_setting_layout.addWidget(self.night_mode_brightness_lineedit, 2, 5)
        self.video_params_setting_layout.addWidget(self.sleep_mode_brightness_label, 3, 4)
        self.video_params_setting_layout.addWidget(self.sleep_mode_brightness_lineedit, 3, 5)

        self.video_params_setting_layout.addWidget(self.icled_type_label, 0, 6)
        self.video_params_setting_layout.addWidget(self.icled_type_combobox, 0, 7)
        self.video_params_setting_layout.addWidget(self.led_r_gain_label, 1, 6)
        self.video_params_setting_layout.addWidget(self.led_r_gain_lineedit, 1, 7)
        self.video_params_setting_layout.addWidget(self.led_g_gain_label, 2, 6)
        self.video_params_setting_layout.addWidget(self.led_g_gain_lineedit, 2, 7)
        self.video_params_setting_layout.addWidget(self.led_b_gain_label, 3, 6)
        self.video_params_setting_layout.addWidget(self.led_b_gain_lineedit, 3, 7)

        self.video_params_setting_layout.addWidget(self.output_frame_width_label, 0, 8)
        self.video_params_setting_layout.addWidget(self.output_frame_width_lineedit, 0, 9)
        self.video_params_setting_layout.addWidget(self.output_frame_height_label, 1, 8)
        self.video_params_setting_layout.addWidget(self.output_frame_height_lineedit, 1, 9)
        self.video_params_setting_layout.addWidget(self.output_fps_label, 2, 8)
        self.video_params_setting_layout.addWidget(self.output_fps_lineedit, 2, 9)

        self.video_params_setting_layout.addWidget(self.video_adj_br_ga_btn, 4, 2, 1, 8)
        self.video_params_setting_layout.addWidget(self.media_adj_crop_btn, 4, 0, 1, 2)

        self.media_control_panel_layout.addWidget(self.play_pause_btn, 0, 1, 1, 2)
        self.media_control_panel_layout.addWidget(self.play_stop_btn, 0, 2, 1, 2)
        self.media_control_panel_layout.addWidget(self.preview_control_btn, 1, 0, 1, 2)
        self.media_control_panel_layout.addWidget(self.sound_control_btn, 1, 2, 1, 2)
        self.media_control_panel_layout.addWidget(self.video_params_setting_widget, 5, 0, 4, 4)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.media_files_tree_widget)
        self.layout.addWidget(self.media_control_panel)
        self.setLayout(self.layout)

    def refresh_internal_media_file_list_tree_widget(self):
        self.media_file_list_internal = []
        for d in self.internal_media_folder:
            self.media_file_list_internal.append(MediaFileList(d))
        # self.media_file_list_internal = MediaFileList(self.internal_media_folder)
        for i in reversed(range(self.internal_media_file_tree_widget_root.childCount())):
            self.internal_media_file_tree_widget_root.removeChild(self.internal_media_file_tree_widget_root.child(i))
        # self.media_files_tree_widget.headerItem().setText(0, "Media Files")
        for f in self.media_file_list_internal[0].filelist:
            internal_file_item = QTreeWidgetItem()
            internal_file_item.setText(0, os.path.basename(f))

            self.gen_internal_media_file_thumbnails(os.path.basename(f))
            self.internal_media_file_tree_widget_root.addChild(internal_file_item)
        # self.refresh_playlist_items()

    def refresh_external_media_file_list_tree_widget(self):
        self.media_file_list_external = []
        for d in self.external_media_folder:
            self.media_file_list_external.append(MediaFileList(d))
        for i in reversed(range(self.external_media_file_tree_widget_root.childCount())):
            self.external_media_file_tree_widget_root.removeChild(self.external_media_file_tree_widget_root.child(i))
        for i in range(len(self.media_file_list_external)):
            log.debug("%s", self.media_file_list_external[i].folder_uri)
            external_folder_tree_widget = QTreeWidgetItem()
            external_folder_tree_widget.setText(0, os.path.basename(self.media_file_list_external[i].folder_uri))
            self.external_media_file_tree_widget_root.addChild(external_folder_tree_widget)
            for f in self.media_file_list_external[i].filelist:
                external_file_item = QTreeWidgetItem()
                external_file_item.setText(0, os.path.basename(f))
                self.gen_external_media_file_thumbnails(self.media_file_list_external[i].folder_uri,
                                                        os.path.basename(f))
                self.external_media_file_tree_widget_root.child(i).addChild(external_file_item)

    def refresh_media_playlist_tree_widget(self):
        for i in reversed(range(self.media_playlist_tree_widget_root.childCount())):
            self.media_playlist_tree_widget_root.removeChild(self.media_playlist_tree_widget_root.child(i))

        for i in range(len(self.media_playlist)):
            log.debug("playlist name : %s", self.media_playlist[i].name)
            playlist_tree_widget = QTreeWidgetItem()
            playlist_tree_widget.setText(0, self.media_playlist[i].name)
            self.media_playlist_tree_widget_root.addChild(playlist_tree_widget)
            for f in self.media_playlist[i].fileslist:
                log.debug("f: %s", f)
                playlist_content_item = QTreeWidgetItem()
                playlist_content_item.setText(0, os.path.basename(f))
                self.media_playlist_tree_widget_root.child(i).addChild(playlist_content_item)

    def gen_internal_media_file_thumbnails(self, base_fname):
        for d in self.internal_media_folder:
            gen_webp_from_video_threading(d, os.path.basename(base_fname))

    def gen_external_media_file_thumbnails(self, folder_path, base_fname):
        gen_webp_from_video_threading(folder_path, os.path.basename(base_fname))
        # gen_webp_from_video_threading(self.external_media_folder, os.path.basename(base_fname))

    ''' show preview widget or not'''

    def mouse_move_on_tree(self, event: QMouseEvent):
        try:
            self.grabMouse()
            # log.debug("%s, %s", event.x(), event.y())
            if self.preview_file_movie is not None:
                self.preview_file_movie.stop()
            if self.media_files_tree_widget.itemAt(event.x(), event.y()) is None:
                if self.media_preview_widget.isVisible() is True:
                    self.media_preview_widget.hide()
                self.releaseMouse()
                return
            else:
                tree_widget_item = self.media_files_tree_widget.itemAt(event.x(), event.y())
                if event.x() < 15 or \
                        event.x() > len(tree_widget_item.text(0)) * self.File_List_Font_Size:
                    if self.media_preview_widget.isVisible() is True:
                        self.media_preview_widget.hide()
                    self.releaseMouse()
                    return
            self.preview_file_name = self.media_files_tree_widget.itemAt(event.x(), event.y()).text(0)
            thumbnail_file_name = hashlib.md5(
                self.preview_file_name.split(".")[0].encode('utf-8')).hexdigest() + ".webp"
            if os.path.exists(
                    self.internal_media_folder[0] + ThumbnailFileFolder + thumbnail_file_name) is False:
                if self.media_preview_widget.isVisible() is True:
                    self.media_preview_widget.hide()
                self.releaseMouse()
                return
            else:
                self.media_preview_widget.setFixedSize(self.Preview_Widget_Width, self.Preview_Widget_Height)
                self.media_preview_widget.setGeometry(self.main_windows.x()
                                                      + self.main_windows.width()
                                                      - self.media_preview_widget.width(),
                                                      self.main_windows.y(),
                                                      self.media_preview_widget.width(),
                                                      self.media_preview_widget.height())

                del self.preview_file_movie
                self.preview_file_movie = QMovie(
                    self.internal_media_folder[0] + ThumbnailFileFolder + thumbnail_file_name)

                self.media_preview_widget.setMovie(self.preview_file_movie)
                self.preview_file_movie.start()
                self.media_preview_widget.show()
        except Exception as e:
            log.debug(e)
        finally:
            self.releaseMouse()

    def internal_media_files_changed(self):
        self.refresh_internal_media_file_list_tree_widget()

    def external_media_files_changed(self):
        os.sync()
        self.external_media_folder = get_mount_points()
        log.debug("%s", self.external_media_folder)
        self.refresh_external_media_file_list_tree_widget()

    def right_click_context_menu(self, position):
        log.debug("right_click_context_menu")
        widgetitem = self.media_files_tree_widget.itemAt(position)
        self.right_clicked_pos = position
        log.debug(" %s", widgetitem.text(0))
        if widgetitem.parent() is None:
            log.debug("Click on Title")
            return
        else:
            if widgetitem.parent().text(0) == self.TAG_Str_Internal_Media:
                log.debug("Internal Media")
                self.show_internal_media_file_popup_menu(self.media_files_tree_widget.mapToGlobal(position))
            elif widgetitem.parent().text(0) == self.TAG_Str_Playlist:
                log.debug("Playlist File")
                self.show_playlist_file_popup_menu(self.media_files_tree_widget.mapToGlobal(position))
            elif widgetitem.parent().parent() is not None:
                if widgetitem.parent().parent().text(0) == self.TAG_Str_External_Media:
                    log.debug("External Media")
                    self.show_external_media_file_popup_menu(self.media_files_tree_widget.mapToGlobal(position))
                elif widgetitem.parent().parent().text(0) == self.TAG_Str_Playlist:
                    log.debug("Playlist Content")
                    self.show_playlist_content_popup_menu(self.media_files_tree_widget.mapToGlobal(position))
            # elif widgetitem.parent().text(0) == self.TAG_Str_Playlist:
            #    log.debug("Playlist")
            # self.show_internal_media_file_popup_menu(self.media_files_tree_widget.mapToGlobal(position))

    def show_internal_media_file_popup_menu(self, pos):
        pop_menu = QMenu()
        try:
            pop_menu.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                                   """
                              QMenu{
                                  button-layout : 2;
                                  font: bold 16pt "Brutal Type";
                                  border: 3px solid #FFA042;
                                  border-radius: 8px;
                                  }
                              """)
        except Exception as e:
            log.error(e)
        play_act = QAction(self.TAG_Str_Popup_Menu_Play, self)
        pop_menu.addAction(play_act)
        del_act = QAction(self.TAG_Str_Popup_Menu_Delete, self)
        pop_menu.addAction(del_act)
        pop_menu.addSeparator()
        add_to_playlist_menu = QMenu(self.TAG_Str_Popup_Menu_Add_to_Playlist)
        try:
            add_to_playlist_menu.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                                               """
                                   QMenu{
                                       button-layout : 2;
                                       font: bold 16pt "Brutal Type";
                                       border: 3px solid #FFA042;
                                       border-radius: 8px;
                                       }
                                   """)
        except Exception as e:
            log.error(e)
        for playlist in self.media_playlist:
            playlist_name = playlist.name
            add_to_playlist_menu.addAction(self.TAG_Str_Popup_Menu_Add_to + playlist_name)
        add_to_playlist_menu.addAction(self.TAG_Str_Popup_Menu_Add_to_New_Playlist)
        pop_menu.addMenu(add_to_playlist_menu)
        pop_menu.triggered[QAction].connect(self.pop_menu_trigger_act)
        pop_menu.exec_(pos)

    def show_playlist_file_popup_menu(self, pos):
        pop_menu = QMenu()
        try:
            pop_menu.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                                   """
                                   QMenu{
                                       button-layout : 2;
                                       font: bold 16pt "Brutal Type";
                                       border: 3px solid #FFA042;
                                       border-radius: 8px;
                                       }
                                   """)
        except Exception as e:
            log.error(e)
        play_act = QAction(self.TAG_Str_Popup_Menu_Play_Playlist, self)
        pop_menu.addAction(play_act)
        del_act = QAction(self.TAG_Str_Popup_Menu_Delete_Playlist, self)
        pop_menu.addAction(del_act)

        pop_menu.triggered[QAction].connect(self.pop_menu_trigger_act)
        pop_menu.exec_(pos)

    def show_playlist_content_popup_menu(self, pos):
        pop_menu = QMenu()
        try:
            pop_menu.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                                   """
                                   QMenu{
                                       button-layout : 2;
                                       font: bold 16pt "Brutal Type";
                                       border: 3px solid #FFA042;
                                       border-radius: 8px;
                                       }
                                   """)
        except Exception as e:
            log.error(e)
        play_act = QAction(self.TAG_Str_Popup_Menu_Play_Playlist, self)
        pop_menu.addAction(play_act)
        del_act = QAction(self.TAG_Str_Popup_Menu_Remove_From_Playlist, self)
        pop_menu.addAction(del_act)
        pop_menu.triggered[QAction].connect(self.pop_menu_trigger_act)
        pop_menu.exec_(pos)

    def show_external_media_file_popup_menu(self, pos):
        pop_menu = QMenu()
        try:
            pop_menu.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                                   """
                              QMenu{
                                  button-layout : 2;
                                  font: bold 16pt "Brutal Type";
                                  border: 3px solid #FFA042;
                                  border-radius: 8px;
                                  }
                              """)
        except Exception as e:
            log.error(e)
        play_act = QAction(self.TAG_Str_Popup_Menu_Copy_To_Internal, self)
        pop_menu.addAction(play_act)
        del_act = QAction(self.TAG_Str_Popup_Menu_Delete, self)
        pop_menu.addAction(del_act)
        ''' I do not want to add external media file to playlist '''

        pop_menu.triggered[QAction].connect(self.pop_menu_trigger_act)
        pop_menu.exec_(pos)

    def pop_menu_trigger_act(self, q):
        log.debug("%s", q.text())
        ''' The function handle all the pop up menu function'''
        if self.TAG_Str_Popup_Menu_Add_to in q.text():
            playlist_name = q.text().split(" ")[2]
            selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
            file_uri_to_add = None
            if selected_widget.parent().text(0) == self.TAG_Str_Internal_Media:
                file_uri_to_add = self.internal_media_folder[0] + "/" + selected_widget.text(0)
            for pl in self.media_playlist:
                if pl.name == playlist_name:
                    pl.add_file_uri_to_playlist(file_uri_to_add)
                    self.refresh_media_playlist_tree_widget()
        elif q.text() == self.TAG_Str_Popup_Menu_Add_to_New_Playlist:
            if self.NewPlaylistDialog is None:
                self.NewPlaylistDialog = NewPlaylistDialog(self.media_playlist)
            self.NewPlaylistDialog.signal_new_playlist_generate.connect(self.slot_new_playlist)
            self.NewPlaylistDialog.show()
        elif q.text() == self.TAG_Str_Popup_Menu_Delete:
            try:
                self.delete_selected_file()
            except Exception as e:
                log.debug(e)
        elif q.text() == self.TAG_Str_Popup_Menu_Copy_To_Internal:
            self.copy_external_file_to_internal()
        elif q.text() == self.TAG_Str_Popup_Menu_Play_Playlist:
            log.debug("Play Playlist not Implemented")
        elif q.text() == self.TAG_Str_Popup_Menu_Delete_Playlist:
            self.delete_selected_playlist()
        elif q.text() == self.TAG_Str_Popup_Menu_Remove_From_Playlist:
            self.remove_file_from_playlist()
        elif q.text() == self.TAG_Str_Popup_Menu_Play:
            selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
            # selected_file_name = selected_widget.text(0)
            select_file_uri = self.internal_media_folder[0] + "/" + selected_widget.text(0)
            self.select_current_file_uri = select_file_uri
            self.media_active_width = 0
            self.media_active_height = 0
            resolution = self.media_engine.get_video_resolution(self.select_current_file_uri)
            log.debug("resolution : %s", resolution)
            if resolution is not None:
                self.media_active_width, self.media_active_height = resolution

            self.media_engine.single_play(self.select_current_file_uri,
                                          active_width=self.media_active_width,
                                          active_height=self.media_active_height)
            '''w, h = get_led_config_from_file_uri("led_wall_resolution",
                                                "led_wall_width", "led_wall_height")
            log.debug("w : %s, h : %s", w, h)
            get_ffmpeg_cmd_with_playing_media_file_("/home/venom/Videos/venom.jpeg", width=480, height=320,
                                                    target_fps="24/1", image_period=20)'''

    def copy_external_file_to_internal(self):
        selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
        selected_file_name = selected_widget.text(0)
        selected_file_uri = (self.TAG_Str_Media_Folder + os.getlogin() + self.TAG_Str_Splash_Mark +
                             selected_widget.parent().text(0) + self.TAG_Str_Splash_Mark + selected_file_name)
        shutil.copy(selected_file_uri, self.internal_media_folder[0] + self.TAG_Str_Splash_Mark + selected_file_name)
        self.refresh_internal_media_file_list_tree_widget()

    def remove_file_from_playlist(self):
        selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
        playlist_name = selected_widget.parent().text(0)
        log.debug('handle playlist_name : %s', playlist_name)
        ''' We do not determinant the name, we determinant the index for remove item'''
        remove_idx = None
        for i in range(selected_widget.parent().childCount()):
            if selected_widget.parent().child(i) == selected_widget:
                log.debug("i : %d", i)
                remove_idx = i
                break
        if remove_idx is None:
            log.error("something wrong with remove index")
            return
        for playlist in self.media_playlist:
            if playlist.name == playlist_name:
                playlist.remove_file_from_playlist_by_idex(remove_idx)
                self.refresh_media_playlist_tree_widget()

    def delete_selected_playlist(self):
        selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
        log.debug("selected_widget.text(0) : %s", selected_widget.text(0))
        playlist_uri_to_delete = None
        playlist_uri_to_delete = self.internal_media_folder[0] + PlaylistFolder + selected_widget.text(0)
        log.debug("playlist_uri_to_delete : %s", playlist_uri_to_delete)
        if os.path.exists(playlist_uri_to_delete) is True:
            os.remove(playlist_uri_to_delete)
            ''' refresh self.media_playlist'''
            self.playlist_files_list = get_playlist_file_list(self.internal_media_folder[0] + PlaylistFolder)
            log.debug("playlist_files_list : %s", self.playlist_files_list)
            self.media_playlist = []
            for file in self.playlist_files_list:
                playlist_tmp = PlayList(file)
                self.media_playlist.append(playlist_tmp)
                ''' refresh media playlist UI'''
            self.refresh_media_playlist_tree_widget()

    def delete_selected_file(self):
        selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
        log.debug("selected_widget.text(0) : %s", selected_widget.text(0))
        file_uri_to_delete = None
        # Internal Media file delete
        if selected_widget.parent().text(0) == self.TAG_Str_Internal_Media:
            file_uri_to_delete = self.internal_media_folder[0] + "/" + selected_widget.text(0)
        # External Media File delete
        elif selected_widget.parent().parent() is not None:
            # External Media File delete
            if selected_widget.parent().parent().text(0) == self.TAG_Str_External_Media:
                file_uri_to_delete = (self.TAG_Str_Media_Folder + os.getlogin() + self.TAG_Str_Splash_Mark
                                      + selected_widget.parent().text(0) + self.TAG_Str_Splash_Mark
                                      + selected_widget.text(0))
        log.debug("file_uri_to_delete : %s", file_uri_to_delete)
        if os.path.exists(file_uri_to_delete) is True:
            os.remove(file_uri_to_delete)
            thumbnail_file_name = hashlib.md5(
                file_uri_to_delete.split(self.internal_media_folder[0] + "/")[1].split(".")[0].encode(
                    'utf-8')).hexdigest() + ".webp"
            thumbnail_file = self.internal_media_folder[0] + ThumbnailFileFolder + thumbnail_file_name
            if os.path.exists(thumbnail_file) is True:
                log.debug("thumbnail_file exists")
                os.remove(thumbnail_file)
            if selected_widget.parent().text(0) == self.TAG_Str_Internal_Media:
                self.refresh_internal_media_file_list_tree_widget()
            elif selected_widget.parent().parent() is not None:
                self.refresh_external_media_file_list_tree_widget()
            # Need to refresh playlist
            for pl in self.media_playlist:
                pl.remove_file_from_playlist(file_uri_to_delete)
            self.refresh_media_playlist_tree_widget()

    def slot_new_playlist(self, new_playlist_name):
        file_uri_add_to_playlist = None
        log.debug("new_playlist_name : %s", new_playlist_name)
        new_playlist_uri = (self.internal_media_folder[0] + PlaylistFolder
                            + new_playlist_name + self.TAG_Str_Playlist_Extension)
        playlist_tmp = PlayList(new_playlist_uri)
        selected_widget = self.media_files_tree_widget.itemAt(self.right_clicked_pos)
        if selected_widget.parent().text(0) == self.TAG_Str_Internal_Media:
            file_uri_add_to_playlist = self.internal_media_folder[0] + "/" + selected_widget.text(0)
        else:
            log.error("From where??")
        # elif selected_widget.parent().text(0) == self.TAG_Str_External_Media:
        #    file_uri_add_to_playlist = self.internal_media_folder[0] + "/" + selected_widget.text(0)
        log.debug("file_uri_add_to_playlist : %s", file_uri_add_to_playlist)
        playlist_tmp.add_file_uri_to_playlist(file_uri_add_to_playlist)
        self.media_playlist.append(playlist_tmp)
        self.refresh_media_playlist_tree_widget()

    def media_play_status_changed(self, status: int, file_uri: str):
        log.debug("status : %d", status)
        log.debug("file_uri : %s", file_uri)
        if status == PlayStatus.Playing:
            self.play_pause_btn.setIcon(self.pause_icon)
            '''if self.media_preview_widget is not None:
                self.media_preview_widget.stop()
                self.media_preview_widget.hide()'''
        elif status == PlayStatus.Pausing:
            self.play_pause_btn.setIcon(self.play_icon)
        elif status == PlayStatus.Stop or status == PlayStatus.Initial:
            self.play_pause_btn.setIcon(self.play_icon)

    def stop_btn_clicked(self):
        log.debug("")
        self.media_engine.resume_playing()
        self.media_engine.stop_play()

    def pause_btn_clicked(self):
        log.debug("")
        if PlayStatus.Playing == self.media_engine.playing_status:
            self.media_engine.pause_playing()
        elif PlayStatus.Pausing == self.media_engine.playing_status:
            self.media_engine.resume_playing()
        elif (PlayStatus.Stop == self.media_engine.playing_status or
              PlayStatus.Initial == self.media_engine.playing_status):
            if self.media_engine.play_single_file_worker is None:
                if self.select_current_file_uri:
                    if os.path.exists(self.select_current_file_uri):
                        self.media_engine.single_play(self.select_current_file_uri,
                                                      active_width=self.media_active_width,
                                                      active_height=self.media_active_height)

    def sound_btn_clicked(self):
        log.debug("")
        if self.sound_control_btn.isChecked():
            self.media_engine.led_video_params.set_play_with_audio(0)
            self.sound_control_btn.setIcon(QIcon('materials/soundOffIcon.png'))
        else:
            self.media_engine.led_video_params.set_play_with_audio(1)
            self.sound_control_btn.setIcon(QIcon('materials/soundOnIcon.png'))

        # move to media_engine
        '''if PlayStatus.Playing == self.media_engine.playing_status:
            if self.media_engine.play_single_file_worker:
                if os.path.exists(self.select_current_file_uri):
                    self.media_engine.stop_play()
                    self.media_engine.single_play(self.select_current_file_uri,
                                                  active_width=self.media_active_width,
                                                  active_height=self.media_active_height,
                                                  audio_active=self.media_engine.led_video_params.get_play_with_audio(),
                                                  preview_visible=self.previewVisibleToggle)'''

    def preview_btn_clicked(self):
        log.debug("")
        if self.preview_control_btn.isChecked():
            self.media_engine.led_video_params.set_play_with_preview(0)
            self.preview_control_btn.setIcon(QIcon('materials/eyeCloseIcon.png'))
        else:
            self.media_engine.led_video_params.set_play_with_preview(1)
            self.preview_control_btn.setIcon(QIcon('materials/eyeOpenIcon.png'))

        # move to media_engine
        '''if PlayStatus.Playing == self.media_engine.playing_status:
            if self.media_engine.play_single_file_worker:
                if os.path.exists(self.select_current_file_uri):
                    self.media_engine.stop_play()
                    self.media_engine.single_play(self.select_current_file_uri,
                                                  active_width=self.media_active_width,
                                                  active_height=self.media_active_height,
                                                  audio_active=self.media_engine.led_video_params.get_play_with_audio(),
                                                  preview_visible=self.previewVisibleToggle)'''

    def adj_media_ctrl_param(self):
        self.media_engine.led_video_params.set_media_file_crop_w(int(self.video_crop_w_lineedit.text()))
        self.media_engine.led_video_params.set_media_file_crop_h(int(self.video_crop_h_lineedit.text()))
        self.media_engine.led_video_params.set_media_file_start_x(int(self.video_crop_x_lineedit.text()))
        self.media_engine.led_video_params.set_media_file_start_y(int(self.video_crop_y_lineedit.text()))
        # self.media_engine.led_video_params.sync_video_param()

        # move to media_engine
        '''if PlayStatus.Playing == self.media_engine.playing_status:
            if self.media_engine.play_single_file_worker:
                if os.path.exists(self.select_current_file_uri):
                    self.media_engine.stop_play()
                    self.media_engine.single_play(self.select_current_file_uri,
                                                  active_width=self.media_active_width,
                                                  active_height=self.media_active_height,
                                                  audio_active=self.media_engine.led_video_params.get_play_with_audio(),
                                                  preview_visible=self.previewVisibleToggle)'''

    def adj_video_br_ga_param(self):
        if (int(self.video_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.video_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.video_brightness_lineedit.setText(str(self.media_engine.led_video_params.get_led_brightness()))
            return
        if (float(self.video_gamma_lineedit.text()) < MIN_FRAME_GAMMA
                or float(self.video_gamma_lineedit.text()) > MAX_FRAME_GAMMA):
            self.video_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))
            return

        if (int(self.day_mode_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.day_mode_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.day_mode_brightness_lineedit.setText(
                str(self.media_engine.led_video_params.get_day_mode_frame_brightness()))

        if (int(self.night_mode_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.night_mode_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.night_mode_brightness_lineedit.setText(
                str(self.media_engine.led_video_params.get_night_mode_frame_brightness()))

        if (int(self.sleep_mode_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.sleep_mode_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.sleep_mode_brightness_lineedit.setText(
                str(self.media_engine.led_video_params.get_sleep_mode_frame_brightness()))

        ''' set led brightness '''
        if self.media_engine.led_video_params.get_led_brightness() != int(self.video_brightness_lineedit.text()):
            self.media_engine.led_video_params.set_led_brightness(int(self.video_brightness_lineedit.text()))
        ''' set led gamma '''
        if self.media_engine.led_video_params.get_led_gamma() != float(self.video_gamma_lineedit.text()):
            # send_message(set_gamma=self.video_gamma_lineedit.text()) # for test
            self.media_engine.led_video_params.set_led_gamma(float(self.video_gamma_lineedit.text()))

        ''' set icled type '''
        if self.media_engine.led_video_params.get_icled_type() != int(self.icled_type_combobox.currentIndex()):
            self.media_engine.led_video_params.set_icled_type(int(self.icled_type_combobox.currentIndex()))

        ''' set led rgb gain '''
        if self.media_engine.led_video_params.get_led_red_gain() != int(self.led_r_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_red_gain(int(self.led_r_gain_lineedit.text()))
        if self.media_engine.led_video_params.get_led_green_gain() != int(self.led_g_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_green_gain(int(self.led_g_gain_lineedit.text()))
        if self.media_engine.led_video_params.get_led_blue_gain() != int(self.led_b_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_blue_gain(int(self.led_b_gain_lineedit.text()))

        ''' set brightness algo '''
        if (self.media_engine.led_video_params.get_frame_brightness_algo() !=
                self.brightness_algo_combobox.currentIndex()):
            log.debug("brightness_algo changed")
            self.media_engine.led_video_params.set_frame_brightness_algo(self.brightness_algo_combobox.currentIndex())

        ''' set sleep mode enable '''
        if (self.media_engine.led_video_params.get_sleep_mode_enable() !=
                self.sleep_mode_enable_combobox.currentIndex()):
            log.debug("sleep_mode changed")
            self.media_engine.led_video_params.set_sleep_mode_enable(self.sleep_mode_enable_combobox.currentIndex())

        ''' set target city'''
        if (self.media_engine.led_video_params.get_target_city_index() !=
                self.target_city_combobox.currentIndex()):
            log.debug("target city changed")
            self.media_engine.led_video_params.set_target_city_index(self.target_city_combobox.currentIndex())

        ''' set led day mode brightness '''
        if (self.media_engine.led_video_params.get_day_mode_frame_brightness() !=
                int(self.day_mode_brightness_lineedit.text())):
            self.media_engine.led_video_params.set_day_mode_frame_brightness(
                int(self.day_mode_brightness_lineedit.text()))

        ''' set led night mode brightness '''
        if (self.media_engine.led_video_params.get_night_mode_frame_brightness() !=
                int(self.night_mode_brightness_lineedit.text())):
            self.media_engine.led_video_params.set_night_mode_frame_brightness(
                int(self.night_mode_brightness_lineedit.text()))

        ''' set led sleep mode brightness '''
        if (self.media_engine.led_video_params.get_sleep_mode_frame_brightness() !=
                int(self.sleep_mode_brightness_lineedit.text())):
            self.media_engine.led_video_params.set_sleep_mode_frame_brightness(
                int(self.sleep_mode_brightness_lineedit.text()))

        ''' Frame width/height/fps'''
        if self.media_engine.led_video_params.get_output_frame_width() != int(self.output_frame_width_lineedit.text()):
            self.media_engine.led_video_params.set_output_frame_width(int(self.output_frame_width_lineedit.text()))

        if (self.media_engine.led_video_params.get_output_frame_height() !=
                int(self.output_frame_height_lineedit.text())):
            self.media_engine.led_video_params.set_output_frame_height(int(self.output_frame_height_lineedit.text()))

        if self.media_engine.led_video_params.get_output_fps() != int(self.output_fps_lineedit.text()):
            self.media_engine.led_video_params.set_output_fps(int(self.output_fps_lineedit.text()))

    def video_params_changed(self):
        log.debug("video_params_changed")

        self.preview_control_btn.setIcon(QIcon(
            'materials/eyeOpenIcon.png' if self.media_engine.led_video_params.get_play_with_preview() == 1
            else 'materials/eyeCloseIcon.png'))
        self.sound_control_btn.setIcon(QIcon(
            'materials/soundOnIcon.png' if self.media_engine.led_video_params.get_play_with_audio() == 1
            else 'materials/soundOffIcon.png'))

        self.video_brightness_lineedit.setText(str(self.media_engine.led_video_params.get_led_brightness()))
        self.video_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))
        self.brightness_algo_combobox.setCurrentIndex(self.media_engine.led_video_params.get_frame_brightness_algo())

        self.sleep_mode_enable_combobox.setCurrentIndex(self.media_engine.led_video_params.get_sleep_mode_enable())
        self.target_city_combobox.setCurrentIndex(self.media_engine.led_video_params.get_target_city_index())
        self.day_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_day_mode_frame_brightness()))
        self.night_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_night_mode_frame_brightness()))
        self.sleep_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_sleep_mode_frame_brightness()))

        self.icled_type_combobox.setCurrentIndex(int(self.media_engine.led_video_params.get_icled_type()))
        self.led_r_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_red_gain()))
        self.led_g_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_green_gain()))
        self.led_b_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_blue_gain()))

        self.output_frame_width_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_width()))
        self.output_frame_height_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_height()))
        self.output_fps_lineedit.setText(str(self.media_engine.led_video_params.get_output_fps()))

        self.video_crop_x_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_x()))
        self.video_crop_y_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_y()))
        self.video_crop_w_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_w()))
        self.video_crop_h_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_h()))
