import hashlib
import os
import shutil

import qdarkstyle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QMouseEvent, QMovie
from PyQt5.QtWidgets import QWidget, QVBoxLayout, \
    QAbstractItemView, QTreeWidgetItem, QLabel, QFrame, QMenu, QAction

from media_engine.media_engine import MediaEngine
from utils.utils_file_access import get_playlist_file_list, get_mount_points, get_led_config_from_file_uri
from ext_qt_widgets.media_file_list import MediaFileList
from ext_qt_widgets.media_playlist import PlayList
from ext_qt_widgets.new_playlist_dialog_widget import NewPlaylistDialog
from ext_qt_widgets.system_file_watcher import FileWatcher
from global_def import log
from ext_qt_widgets.custom_tree_widget import CTreeWidget
from media_configs.media_path_configs import *
from utils.gen_thumbnails import gen_webp_from_video_threading
from utils.utils_ffmpy import get_ffmpeg_cmd_with_playing_media_file_


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
        self.main_windows = _main_window
        self.frame = _frame
        self.media_engine = media_engine
        self.media_engine.test()

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
                self.gen_external_media_file_thumbnails(self.media_file_list_external[i].folder_uri, os.path.basename(f))
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
            log.debug("Play not Implemented")
            w, h = get_led_config_from_file_uri("led_wall_resolution",
                                                "led_wall_width", "led_wall_height")
            log.debug("w : %s, h : %s", w, h)
            # get_ffmpeg_cmd_with_playing_media_file_("/home/venom/Videos/venom.jpeg", width=480, height=320)

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
