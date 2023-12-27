import os

from PyQt5.QtCore import QObject
from global_def import log


class PlayList(QObject):
    def __init__(self, name):
        self.name_with_path = name
        self.name = os.path.basename(self.name_with_path)
        self.fileslist = []
        if os.path.exists(self.name_with_path):
            self.load_playlist(self.name_with_path)
        else:
            self.add_file_uri_to_playlist(None)

    def load_playlist(self, file_uri):
        file = open(file_uri, 'r')
        lines = file.readlines()
        for line in lines:
            if len(line) > 1:
                self.fileslist.append(line.strip())

    def add_file_uri_to_playlist(self, file_uri):
        if file_uri is not None:
            self.fileslist.append(file_uri)
            self.playlist_sync_file()
        else:
            file = open(self.name_with_path, "w")
            file.truncate()

    def playlist_sync_file(self):
        file = open(self.name_with_path, "w")
        for i in self.fileslist:
            file.write(i + "\n")
        file.truncate()

    def del_playlist_file(self):
        log.debug("del_playlist_file")
        if os.path.exists(self.name_with_path):
            log.debug("del playlist : %s", self.name_with_path)
            os.remove(self.name_with_path)

    def remove_file_from_playlist(self, file_need_to_remove):
        log.debug("ori fileslist : %s", self.fileslist)
        for i in self.fileslist:
            if i == file_need_to_remove:
                self.fileslist.remove(i)
        log.debug("after fileslist : %s", self.fileslist)
        self.playlist_sync_file()

    def __del__(self):
        log.debug("playlist del")
