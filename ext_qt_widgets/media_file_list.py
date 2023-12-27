from PyQt5.QtCore import QObject
from utils.utils_file_access import *
from global_def import log


class MediaFileList(QObject):
    SUPPORT_FILE_EXTENSION_STR_LIST = ["mp4", "jpg", "jpeg", "png"]

    def __init__(self, uri):
        super().__init__()

        self.folder_uri = uri
        # log.debug("self.folder_uri : %s", self.folder_uri)
        self.filelist = self.get_media_file_list(self.folder_uri)
        # log.debug("file_list = %s", self.filelist)

    def get_media_file_list(self, abs_dir_path: str):
        file_list = []
        for s in self.SUPPORT_FILE_EXTENSION_STR_LIST:
            file_list += (glob.glob(self.folder_uri + "/*." + s))
        return file_list
