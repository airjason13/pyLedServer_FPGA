import enum

from PyQt5.QtCore import QObject
from global_def import log

class FPGAClient(QObject):
    STR_VERSION_UNKNOWN = "unknown"
    STR_UNDEFINED = "undefined"

    class DataDefineStatus(enum.IntEnum):
        unknown = -1
        undefined = 0
        defined = 1

    def __init__(self, client_id, **kwargs):
        super(FPGAClient, self).__init__(**kwargs)
        self.i_id = client_id
        log.debug("self.i_id : %d", self.i_id)
        self.s_version = self.STR_VERSION_UNKNOWN
        self.i_status = self.DataDefineStatus.unknown

    def set_version(self, version: str):
        self.s_version = version

    def set_data_status(self, status: enum):
        self.i_status = status





