from PyQt5.QtCore import QObject, pyqtSignal, QFileSystemWatcher
from global_def import log


class FileWatcher(QObject):
    signal_folder_changed = pyqtSignal(str)

    def __init__(self, paths: list, **kwargs):
        super(FileWatcher, self).__init__(**kwargs)
        self.watch_paths = paths
        self.file_watcher = []
        log.debug("watch paths : %s", self.watch_paths)
        self.watcher = QFileSystemWatcher(self.watch_paths)
        self.watcher.directoryChanged.connect(self.directory_changed)

    def directory_changed(self, path):
        log.debug("path :%s", path)
        self.signal_folder_changed.emit(path)

    def install_folder_changed_slot(self, qt_slot):
        log.debug("")
        self.signal_folder_changed.connect(qt_slot)