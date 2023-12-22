import hashlib
import os
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QMouseEvent, QMovie
from PyQt5.QtWidgets import QWidget, QVBoxLayout, \
    QAbstractItemView, QTreeWidgetItem, QLabel, QFrame

import utils.utils_file_access
from ext_qt_widgets.media_file_list import MediaFileList
from ext_qt_widgets.system_file_watcher import FileWatcher
from global_def import log
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

    def __init__(self, _main_window, _frame: QWidget, _name, **kwargs):
        super(MediaFilesPage, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame
        self.frame.setMouseTracking(True)
        self.widget = QWidget(self.frame)
        self.name = _name
        self.media_files_tree_widget = None
        self.layout = None

        ''' 檔案預覽畫面縮圖 '''
        self.preview_file_name = None
        self.preview_file_movie = None
        self.internal_media_file_tree_widget_root = None
        self.external_media_file_tree_widget_root = None

        ''' media file list internal '''
        self.internal_media_folder = []
        self.internal_media_folder.append(os.path.expanduser("~" + MediaFileFolder))
        self.media_file_list_internal = []
        for d in self.internal_media_folder:
            self.media_file_list_internal.append(MediaFileList(d))
        log.debug("mount point : %s", utils.utils_file_access.get_mount_points())
        self.external_media_folder = utils.utils_file_access.get_mount_points()
        self.media_file_list_external = []
        for d in self.external_media_folder:
            self.media_file_list_external.append(MediaFileList(d))

        self.init_ui()

        media_preview_widget = QLabel()
        media_preview_widget.setFrameShape(QFrame.StyledPanel)
        media_preview_widget.setWindowFlags(Qt.ToolTip)
        media_preview_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        media_preview_widget.hide()
        self.media_preview_widget = media_preview_widget

        ''' install file watcher signal/slot'''
        self.internal_file_watcher = FileWatcher(self.internal_media_folder)
        self.internal_file_watcher.install_folder_changed_slot(self.internal_media_files_changed)
        self.external_file_watcher = FileWatcher([self.TAG_Str_Media_Folder + os.getlogin()])
        self.external_file_watcher.install_folder_changed_slot(self.external_media_files_changed)

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
        '''self.media_files_tree_widget.itemClicked.connect(self.file_selected)
        self.media_files_tree_widget.itemChanged.connect(self.file_changed)
        self.media_files_tree_widget.itemEntered.connect(self.file_item_entered)
        self.media_files_tree_widget.itemActivated.connect(self.file_item_activated)
        self.media_files_tree_widget.itemSelectionChanged.connect(self.file_item_selection_changed)
        self.media_files_tree_widget.currentItemChanged.connect(self.file_item_currentItemChanged)'''

        ''' Handle Internal Media Folder '''
        self.internal_media_file_tree_widget_root = QTreeWidgetItem(self.media_files_tree_widget)

        self.internal_media_file_tree_widget_root.setText(0, self.TAG_Str_Internal_Media)
        self.refresh_internal_media_file_list_tree_widget()

        ''' Handle External Media Folder '''
        self.external_media_file_tree_widget_root = QTreeWidgetItem(self.media_files_tree_widget)
        self.external_media_file_tree_widget_root.setText(0, self.TAG_Str_External_Media)
        self.refresh_external_media_file_list_tree_widget()

        self.media_files_tree_widget.addTopLevelItem(self.internal_media_file_tree_widget_root)
        self.media_files_tree_widget.addTopLevelItem(self.external_media_file_tree_widget_root)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.media_files_tree_widget)
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
        # self.media_file_list_external = MediaFileList(self.external_media_folder)
        for i in reversed(range(self.external_media_file_tree_widget_root.childCount())):
            self.external_media_file_tree_widget_root.removeChild(self.external_media_file_tree_widget_root.child(i))
        # self.media_files_tree_widget.headerItem().setText(0, "Media Files")
        for i in range(len(self.media_file_list_external)):
            log.debug("%s", self.media_file_list_external[i].folder_uri)
            external_folder_tree_widget = QTreeWidgetItem()
            external_folder_tree_widget.setText(0, os.path.basename(self.media_file_list_external[i].folder_uri))
            self.external_media_file_tree_widget_root.addChild(external_folder_tree_widget)
            for f in self.media_file_list_external[i].filelist:
                external_file_item = QTreeWidgetItem()
                external_file_item.setText(0, os.path.basename(f))
                self.gen_external_media_file_thumbnails(self.media_file_list_external[i].folder_uri, os.path.basename(f))
                self.external_media_file_tree_widget_root.child(i).addChild(external_file_item)
        # self.refresh_playlist_items()

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
        self.external_media_folder = utils.utils_file_access.get_mount_points()
        log.debug("%s", self.external_media_folder)
        self.refresh_external_media_file_list_tree_widget()
