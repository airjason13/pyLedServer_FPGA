import enum
from FPGA_protocol.protocol2 import FPGACmdCenter
from PyQt5.QtCore import QObject
from global_def import log


class FPGAClient(QObject):
    STR_VERSION_UNKNOWN = "unknown"
    STR_UNDEFINED = "undefined"
    STR_STATUS_DEFINED = "Status Defined"
    STR_STATUS_UNDEFINED = "Status Undefined"

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

        ret, self.s_version = self.read_cmd_str("stringVersion")

        ret, self.i_framewidth = self.read_cmd_int("frameWidth")
        ret, self.i_frameheight = self.read_cmd_int("frameHeight")
        ret, self.i_current_gamma_index = self.read_cmd_int("currentGammaTable")
        # log.debug("self.i_current_gamma_index : %d", self.i_current_gamma_index)
        self.i_status = self.checkstatus()
        if self.i_status > 0:
            self.s_status = self.STR_STATUS_DEFINED
        else:
            self.s_status = self.STR_STATUS_UNDEFINED
        self.s_controls = "Frame_W:{}, Frame_H:{},Gamma_index:{}".format(
            str(self.i_framewidth), str(self.i_frameheight), str(self.i_current_gamma_index))

        log.debug("self.s_controls : %s", self.s_controls)

    def checkstatus(self) -> int:
        if self.i_framewidth != 0 and self.i_frameheight != 0 and 22 > self.i_current_gamma_index > 0:
            return self.DataDefineStatus.defined
        else:
            return self.DataDefineStatus.undefined


    def set_version(self, version: str):
        self.s_version = version

    def set_data_status(self, status: enum):
        self.i_status = status

    def write_cmd(self, register_name: str, value: str) -> int:
        ret = self.fpga_cmd_center.write_fpga_register(self.i_id, register_name, value)
        return ret

    def read_cmd_int(self, register_name: str) -> (int, int):
        ret, i_value = self.fpga_cmd_center.read_fpga_register(self.i_id, register_name)
        return ret, i_value

    def read_cmd_str(self, register_name: str) -> (int, str):
        ret, b_value = self.fpga_cmd_center.read_fpga_register_bytes(self.i_id, register_name)
        str_value = b_value.decode()
        return ret, str_value



