import enum
from FPGA_protocol.protocol2 import FPGACmdCenter
from PyQt5.QtCore import QObject
from global_def import log


class FPGAClient(QObject):
    STR_VERSION_UNKNOWN = "unknown"
    STR_UNDEFINED = "undefined"

    class DataDefineStatus(enum.IntEnum):
        unknown = -1
        undefined = 0
        defined = 1

    def __init__(self, client_id, fpga_cmd_center: FPGACmdCenter, **kwargs):
        super(FPGAClient, self).__init__(**kwargs)
        self.i_id = client_id
        log.debug("self.i_id : %d", self.i_id)
        self.fpga_cmd_center = fpga_cmd_center
        self.s_version = self.STR_VERSION_UNKNOWN
        self.i_status = self.DataDefineStatus.unknown

    def set_version(self, version: str):
        self.s_version = version

    def set_data_status(self, status: enum):
        self.i_status = status

    def write_cmd(self, register_name: str, value: str) -> int:
        ret = self.fpga_cmd_center.write_fpga_register(self.i_id, register_name, value)
        return ret

    def read_cmd(self, register_name: str) -> (int, str):
        ret, value = self.fpga_cmd_center.read_fpga_register(self.i_id, register_name)
        return ret, value



