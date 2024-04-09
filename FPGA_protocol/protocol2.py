# protocol2.0 2024/02/16 by Doris
import enum

from global_def import log  # import log_utils # utils.log_utils
import socket
import selectors
import struct
import binascii
import threading
import time
import os
import json
import random
# import gammaTable

from FPGA_protocol.ethernet import *

# log = log_utils.logging_init(__file__) # utils.log_utils.logging_init(__file__)

# with open("dataFPGA.json", "r") as jsonFile:
#    data = json.load(jsonFile)

protocolDict = {"preamble": b'\x55\x55\x55\x55\x55\x55\x55',
                "sof": b'\xD5',
                "interface": 'enp55s0',
                "broadcast": b'\x00\x00\x00\x00\x00\x00',
                "sourceAddress": b'\x00\x00\x00\x00\x00\x01',
                "destinationAddress": b'\x00\x00\x00\x00\x00\x0c',
                "crc": b'\xcc\xcc\xcc\xcc'}

flowCtrlDict = {"setID": b'\x10',
                "OTA": b'\x11',
                "imageFlush": b'\x12',
                "otaFinish": b'\x13',
                "writeRegister": b'\x1E',
                "readRegister": b'\x1F',
                "OTA_ack": b'\x91',
                "otaFinish_ack": b'\x93',
                "writeRegister_ack": b'\x9E',
                "readRegister_ack": b'\x9F'}

# b'\x00\x00\x00\x00'            
dataAddressDict = {"deviceID": b'\x00\x00\x00\x00',
                   "flashControl": b'\x03\x00\x00\x00',
                   "UTC": b'\x04\x00\x00\x00',
                   "MD5": b'\x08\x00\x00\x00',
                   "currentGammaTable": b'\x18\x00\x00\x00',
                   "frameWidth": b'\x19\x00\x00\x00',
                   "frameHeight": b'\x1B\x00\x00\x00',
                   "currentGain": b'\x1D\x00\x00\x00',
                   "panelWay": b'\x21\x00\x00\x00',
                   "ledArrangement": b'\x22\x00\x00\x00',
                   "stringVersion": b'\x30\x00\x00\x00',
                   "gammaTable": b'\x00\x20\x00\x00',
                   "gammaTable_r": b'\x00\x20\x00\x00',
                   "gammaTable_g": b'\x00\x22\x00\x00',
                   "gammaTable_b": b'\x00\x24\x00\x00',
                   "test": b'\x11\x22\x33\x44'}


def setPort(dataAdd, channel) -> bytes:
    channel = int(channel) * 0x0A
    dataAdd = int.from_bytes(dataAdd, "big")
    portDataAdd = (dataAdd + channel).to_bytes(4, 'little')
    return portDataAdd
    # self.sendCMD(portDataAdd, 2, data) # len固定為2


def get_gamma_table_address(base_addr: bytes, index: int) -> bytes:
    int_offset = index * 0x0600  # 1024 = 256*4
    int_base_addr = int.from_bytes(base_addr, "little")  # little?big?
    # print("int_offset + int_base_addr : ", int_offset + int_base_addr)
    # print("(int_offset + int_base_addr).to_bytes(4, 'little') : ", (int_offset + int_base_addr).to_bytes(4, "little"))
    return (int_offset + int_base_addr).to_bytes(4, "little")


portDataAddressDict = {"numberOfPixel": b'\x00\x03\x00\x00',
                       "startX": b'\x00\x03\x00\x02',
                       "startY": b'\x00\x03\x00\x04',
                       "portWidth": b'\x00\x03\x00\x06',
                       "portHeight": b'\x00\x03\x00\x08'}

dataLenDict = {"deviceID": 1,
               "flashControl": 1,
               "UTC": 4,
               "MD5": 16,
               "currentGammaTable": 1,
               "frameWidth": 2,
               "frameHeight": 2,
               "currentGain": 4,
               "panelWay": 1,
               "ledArrangement": 2,
               "stringVersion": 16,
               "gammaTable": 512,  # one time for one gamma table #98304,
               "channelSetting": 2  # lens of led layout parameters (pixels/width/height/start_x/start_y )
               }

# handle layout parameters of fpga
for i in range(64):
    dataAddressDict["numberOfPixel_p{}".format(str(i))] = setPort(portDataAddressDict["numberOfPixel"], i)
    dataLenDict["numberOfPixel_p{}".format(str(i))] = 2
    dataAddressDict["startX_p{}".format(str(i))] = setPort(portDataAddressDict["startX"], i)
    dataLenDict["startX_p{}".format(str(i))] = 2
    dataAddressDict["startY_p{}".format(str(i))] = setPort(portDataAddressDict["startY"], i)
    dataLenDict["startY_p{}".format(str(i))] = 2
    dataAddressDict["portWidth_p{}".format(str(i))] = setPort(portDataAddressDict["portWidth"], i)
    dataLenDict["portWidth_p{}".format(str(i))] = 2
    dataAddressDict["portHeight_p{}".format(str(i))] = setPort(portDataAddressDict["portHeight"], i)
    dataLenDict["portHeight_p{}".format(str(i))] = 2

# handle gamma table
for i in range(64):
    dataAddressDict["gammaTable_r{}".format(str(i))] = get_gamma_table_address(dataAddressDict["gammaTable_r"], i)
    dataLenDict["gammaTable_r{}".format(str(i))] = 512
    dataAddressDict["gammaTable_g{}".format(str(i))] = get_gamma_table_address(dataAddressDict["gammaTable_g"], i)
    dataLenDict["gammaTable_g{}".format(str(i))] = 512
    dataAddressDict["gammaTable_b{}".format(str(i))] = get_gamma_table_address(dataAddressDict["gammaTable_b"], i)
    dataLenDict["gammaTable_b{}".format(str(i))] = 512


def dump_register_address():
    for k, v in dataAddressDict.items():
        log.debug("%s, %08x", k, int.from_bytes(v, byteorder='little'))


def get_register_address(register_name: str) -> int:  # need to convert to hex by caller
    for k, v in dataAddressDict.items():
        if k == register_name:
            log.debug("%s, %08x", k, int.from_bytes(v, byteorder='little'))
            break
    return int.from_bytes(v, byteorder='little')


panelWayDict = {"R_U_L_U": '0000',
                "L_U_R_U": '0001',
                "R_D_L_D": '0002',
                "L_D_R_D": '0003',
                "U_R_D_R": '0004',
                "U_L_D_L": '0005',
                "D_R_U_R": '0006',
                "D_L_U_L": '0007'}

ledArrangementDict = {"RGB": '00',
                      "RBG": '01',
                      "GRB": '02',
                      "GBR": '03',
                      "BGR": '04',
                      "BRG": '05'}


class FPGAJsonParams(str):
    params_list = ['deviceID',  # not register
                   'UTC',
                   'MD5',
                   "currentGammaTable",
                   'frameWidth',
                   'frameHeight',
                   'currentGain',
                   'ledArrangement',
                   'stringVersion',
                   ]


# for test only
class FPGACommonRegTestParams(str):
    params_list = ['deviceID',  # not register
                   'UTC',
                   'MD5',
                   "currentGammaTable",
                   'frameWidth',
                   'frameHeight',
                   'currentGain',
                   'panelWay',
                   'ledArrangement',
                   ]


fpga_test_value_opt1 = {
    "deviceID": None,
    "UTC": "1234",
    "MD5": None,
    "currentGammaTable": "1",
    "frameWidth": "160",
    "frameHeight": "48",
    "currentGain": str(int("010101", 16)),  # "1111",
    "panelWay": "3",
    "ledArrangement": "4"
}

fpga_test_value_opt2 = {
    "deviceID": None,
    "UTC": "1234",
    "MD5": None,
    "currentGammaTable": "1",
    "frameWidth": "160",
    "frameHeight": "48",
    "currentGain": str(int("010101", 16)),  # "1111",
    "panelWay": "0",
    "ledArrangement": "4"
}

fpga_test_value = [fpga_test_value_opt1, fpga_test_value_opt2]

fpga_test_layout_value_opt1 = {
    "numberOfPixel": "900",
    "startX": "79",
    "startY": "0",
    "portWidth": "80",
    "portHeight": "12"
}

fpga_test_layout_value_opt2 = {
    "numberOfPixel": "900",
    "startX": "79",
    "startY": "0",
    "portWidth": "80",
    "portHeight": "12"
}

fpga_test_layout_value = [fpga_test_layout_value_opt1,
                          fpga_test_layout_value_opt2]


class FPGALayoutRegParams(str):
    params_list = ["numberOfPixel_p",
                   "startX_p",
                   "startY_p",
                   "portWidth_p",
                   "portHeight_p"
                   ]


# set port data address
'''def init_fpga_layout_register(total_port_num=64):
    for i in range(total_port_num):
        dataAddressDict["numberOfPixel_p{}".format(str(i))] = setPort(portDataAddressDict["numberOfPixel"], i)
        dataAddressDict["startX_p{}".format(str(i))] = setPort(portDataAddressDict["startX"], i)
        dataAddressDict["startY_p{}".format(str(i))] = setPort(portDataAddressDict["startY"], i)
        dataAddressDict["portWidth_p{}".format(str(i))] = setPort(portDataAddressDict["portWidth"], i)
        dataAddressDict["portHeight_p{}".format(str(i))] = setPort(portDataAddressDict["portHeight"], i)'''


# 設定要傳的raw data資料
class setRaw(threading.Thread):
    # 初始化各項欄位資料
    def __init__(self, interface, sourceAdd, destinationAdd, packageIndex, flowCtrl):
        threading.Thread.__init__(self)
        # OTA packageIndex = 0
        self.packageIndex = packageIndex  # 封包順序，現在用來比對是否為同一個ACK封包
        self.interface = interface  # 網路界面
        self.sourceAdd = sourceAdd  # 主控
        # self.destinationAdd = destinationAdd
        # print("destinationAdd = ", destinationAdd)

        # turn data type to byte
        if isinstance(destinationAdd, bytes):
            self.destinationAdd = destinationAdd
        else:
            # turn int -> hex -> byte (6 bytes)
            tempLen = '0'
            for i in range(12 - len(destinationAdd)):
                tempLen = '0' + tempLen

            self.destinationAdd = int(tempLen + destinationAdd).to_bytes(6, 'big')
            # print("destinationAdd = ", self.destinationAdd)
        self.flowCtrl = flowCtrl
        self.numberOfDataByte = 0

    def sendOTA(self, rawDatas):
        dataLen = ETH_DATA_LEN - ETH_TLEN * 5  # ETH_DATA_LEN = 1500, ETH_TLEN = 2, 2 byte
        dataAddLen = 0  # 2 byte
        # print('file:', rawDatas)
        with open(rawDatas, 'rb') as f:
            fileSize = os.path.getsize(rawDatas)
            # print('fileSize = ', fileSize)
            for i in range(0, fileSize, dataLen):
                # 判斷是否為最後一筆資料
                if (i + dataLen) > fileSize:
                    dataLen = fileSize - i
                    data = f.read(fileSize - i)
                    # data = data[::-1]    # LSB
                    dataAddLen = dataAddLen - dataLen + len(data)  # Address 4 bytes
                    data = dataAddLen.to_bytes(4, 'little') + data  # Address 4 bytes + OTA data
                    self.numberOfDataByte = len(data)
                    self.sendSocket(data)
                    # send OTA finish
                    self.flowCtrl = flowCtrlDict["otaFinish"]
                    self.numberOfDataByte = 1
                    self.sendSocket(b'\x00')
                    break

                data = f.read(dataLen)
                # data = data[::-1]    # LSB
                data = dataAddLen.to_bytes(4, 'little') + data
                self.numberOfDataByte = len(data)
                # print('numberOfDataByte = ', self.numberOfDataByte)
                self.sendSocket(data)
                dataAddLen += dataLen
                # packageIndex累加到ff後，歸零
                if self.packageIndex >= 255:
                    self.packageIndex = 0
                else:
                    self.packageIndex += 1

    def send_read_cmd(self, dataAdd: bytes, dataLen: int, rawDatas: str):
        # 長度不夠補0
        if len(rawDatas) < 4:
            zero = 4 - len(rawDatas)
            # rawDatas = rawDatas + bytearray(zero)
            rawDatas = zero * '0' + rawDatas

        # print("rawDatas : ", rawDatas)
        bytes_rawDatas = int(rawDatas).to_bytes(2, 'little')  # str -> byte, LSB
        # rawDatas = bytearray.fromhex(rawDatas)[::-1]    # str -> byte, LSB
        rawData = dataAdd + bytes_rawDatas
        self.numberOfDataByte = len(rawData)
        self.sendSocket(rawData)

    '''def send_read_cmd_ori(self, dataAdd: bytes, dataLen=2, rawDatas='2'):
        # 長度不夠補0
        if len(rawDatas) < (dataLen * 2):
            zero = (dataLen * 2) - len(rawDatas)
            # rawDatas = rawDatas + bytearray(zero)
            rawDatas = zero * '0' + rawDatas

        # print("rawDatas : ", rawDatas)
        rawDatas = int(rawDatas).to_bytes(dataLen, 'little')  # str -> byte, LSB
        # rawDatas = bytearray.fromhex(rawDatas)[::-1]    # str -> byte, LSB 
        # print('rawDatas = ', rawDatas)
        rawData = dataAdd + rawDatas
        # print("rawData : ", rawData)
        self.numberOfDataByte = len(rawData)
        self.sendSocket(rawData)'''

    def send_write_cmd(self, dataAdd: bytes, dataLen: int, rawDatas: str):
        # 長度不夠補0
        if len(rawDatas) < (dataLen * 2):
            zero = (dataLen * 2) - len(rawDatas)
            # rawDatas = rawDatas + bytearray(zero)
            rawDatas = zero * '0' + rawDatas
            # print('rawDatas + bytearray(zero) = ', rawDatas)

        # print("rawDatas : ", rawDatas)
        rawDatas = int(rawDatas).to_bytes(dataLen, 'little')  # str -> byte, LSB
        # rawDatas = bytearray.fromhex(rawDatas)[::-1]    # str -> byte, LSB
        # print('rawDatas = ', rawDatas)
        rawData = dataAdd + rawDatas
        # print("rawData : ", rawData)
        self.numberOfDataByte = len(rawData)
        self.sendSocket(rawData)

    def send_ota_finish_data(self):
        self.numberOfDataByte = 1
        self.sendSocket(b'\x00')

    def send_ota_data(self, data: bytes):
        self.numberOfDataByte = len(data)
        self.sendSocket(data)

    def send_write_cmd_with_bytes(self, dataAdd: bytes, dataLen: int, rawDatas: bytes):
        # 長度不夠補0
        '''if len(rawDatas) < (dataLen * 2):
            zero = (dataLen * 2) - len(rawDatas)
            # rawDatas = rawDatas + bytearray(zero)
            rawDatas = zero * '0' + rawDatas
            # print('rawDatas + bytearray(zero) = ', rawDatas)'''

        # print("rawDatas : ", rawDatas)
        # rawDatas = int(rawDatas).to_bytes(dataLen, 'little')  # str -> byte, LSB
        # rawDatas = bytearray.fromhex(rawDatas)[::-1]    # str -> byte, LSB
        # print('rawDatas = ', rawDatas)
        rawData = dataAdd + rawDatas
        # print("rawData : ", rawData)
        self.numberOfDataByte = len(rawData)
        self.sendSocket(rawData)

    def sendSocket(self, rawData):
        try:
            with socket.socket(socket.AF_PACKET, socket.SOCK_RAW) as client_socket:
                # Bind an interface
                client_socket.bind((self.interface, 0))

                # Send a frame
                client_socket.sendall(
                    # Pack in network byte order (frame)
                    struct.pack('!6s6ssHs' + str(self.numberOfDataByte) + 's4s',
                                self.destinationAdd,
                                self.sourceAdd,
                                self.packageIndex.to_bytes(1, 'big'),
                                self.numberOfDataByte,  # number of data byte
                                self.flowCtrl,
                                rawData,
                                protocolDict["crc"]))
        except Exception as e:
            log.fatal(e)


# 攔截ACK封包
class getRaw(threading.Thread):
    def __init__(self, interface, flowCtrl, packageIndex):
        threading.Thread.__init__(self)
        self.interface = interface
        self.flowCtrl = flowCtrl
        self.packageIndex = packageIndex
        self.payload = None
        self.ackStatus = None
        self.stopThreads = False
        self.read_to_recv = False
        self.selector = None

    def set_stop(self, status: bool):
        self.stopThreads = status

    def run(self):
        try:
            with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as server_socket:
                # Bind the interface
                server_socket.bind((self.interface, 0))
                with selectors.DefaultSelector() as self.selector:

                    # Resister the socket for selection, monitoring it for I/O events
                    self.selector.register(server_socket.fileno(), selectors.EVENT_READ)

                    while True:
                        if self.stopThreads:
                            log.debug("fpga wait cmd ack stopThreads break.")
                            break
                        # Wait until the socket become readable
                        ready = self.selector.select()
                        if ready:
                            # Receive a frame, ETH_FRAME_LEN = 1514
                            frame = server_socket.recv(ETH_FRAME_LEN)
                            # Extract a header, ETH_HLEN = 14
                            header = frame[:17]
                            # Unpack an Ethernet header in network byte order
                            src, dst, index, number, fc, ack = struct.unpack('!6s6ss2sss', header)
                            dataLen = int.from_bytes(number, "big")
                            packageIndex = int.from_bytes(index, "big")
                            if src == protocolDict["sourceAddress"]:
                                if ack == b'\xA0':

                                    if fc == self.flowCtrl and packageIndex == self.packageIndex:
                                        if self.flowCtrl == flowCtrlDict["readRegister_ack"]:
                                            # Extract a payload
                                            self.payload = frame[17:17 + dataLen - 1]
                                            self.payload = int.from_bytes(self.payload, "little")
                                        self.ackStatus = 0
                                    return
                                elif ack == b'\x01':
                                    log.debug("CRC Error, self.packageIndex : %d", self.packageIndex)
                                    # self.ackStatus = -1  # ignore the data length error,and let the r/w cmd send again
                                    # return
                                elif ack == b'\x02':
                                    log.debug("Data Length Error, self.packageIndex : %d", self.packageIndex)
                                    # self.ackStatus = -1  # ignore the data length error,and let the r/w cmd send again
                                    # return
                                else:
                                    log.debug("ACK response Error, self.packageIndex : %d", self.packageIndex)
                                    # self.ackStatus = -1  # ignore the data length error,and let the r/w cmd send again
                                    # return
        except Exception as e:
            log.fatal(e)


class getRaw_Bytes(threading.Thread):
    def __init__(self, interface, flowCtrl, packageIndex):
        threading.Thread.__init__(self)
        self.interface = interface
        self.flowCtrl = flowCtrl
        self.packageIndex = packageIndex
        self.payload = None
        self.ackStatus = None
        self.stopThreads = False
        self.read_to_recv = False
        self.selector = None

    def set_stop(self, status: bool):
        self.stopThreads = status

    def run(self):
        try:
            with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as server_socket:
                # Bind the interface
                server_socket.bind((self.interface, 0))
                with selectors.DefaultSelector() as self.selector:

                    # Resister the socket for selection, monitoring it for I/O events
                    self.selector.register(server_socket.fileno(), selectors.EVENT_READ)

                    while True:
                        if self.stopThreads:
                            log.debug("fpga wait cmd ack stopThreads break.")
                            break
                        # Wait until the socket become readable
                        ready = self.selector.select()
                        if ready:
                            # Receive a frame, ETH_FRAME_LEN = 1514
                            frame = server_socket.recv(ETH_FRAME_LEN)
                            # Extract a header, ETH_HLEN = 14
                            header = frame[:17]
                            # Unpack an Ethernet header in network byte order
                            src, dst, index, number, fc, ack = struct.unpack('!6s6ss2sss', header)
                            dataLen = int.from_bytes(number, "big")
                            packageIndex = int.from_bytes(index, "big")
                            if src == protocolDict["sourceAddress"]:
                                if ack == b'\xA0':

                                    if fc == self.flowCtrl and packageIndex == self.packageIndex:
                                        if self.flowCtrl == flowCtrlDict["readRegister_ack"]:
                                            # Extract a payload
                                            self.payload = frame[17:17 + dataLen - 1]
                                            # self.payload = int.from_bytes(self.payload, "little")
                                        self.ackStatus = 0
                                    return
                                elif ack == b'\x01':
                                    log.debug("CRC Error, self.packageIndex : %d", self.packageIndex)
                                    # self.ackStatus = -1  # ignore the data length error,and let the r/w cmd send again
                                    # return
                                elif ack == b'\x02':
                                    log.debug("Data Length Error, self.packageIndex : %d", self.packageIndex)
                                    # self.ackStatus = -1  # ignore the data length error,and let the r/w cmd send again
                                    # return
                                else:
                                    log.debug("ACK response Error, self.packageIndex : %d", self.packageIndex)
                                    # self.ackStatus = -1  # ignore the data length error,and let the r/w cmd send again
                                    # return
        except Exception as e:
            log.fatal(e)


class FPGACmdCenter:
    def __init__(self, interface, server_addr, rw_max_count=10, ack_wait_time=0.03, debug=False):
        self.eth_if = interface
        self.write_cmd = None
        self.read_cmd = None
        self.pkg_index = 0  # from 0
        self.server_addr = server_addr
        self.rw_max_count = rw_max_count
        self.ack_wait_time = ack_wait_time
        self.lock = threading.Lock()
        self.lock_time = self.rw_max_count * self.ack_wait_time
        self.debug = debug

    def reset_cmd_set(self):
        self.write_cmd = None
        self.read_cmd = None

    def pkg_index_addon(self):
        if self.pkg_index >= 0x80:  # 0xff:
            self.pkg_index = 0
        self.pkg_index += 1

    ''' '''

    def set_fpga_id_broadcast(self, start_id: int):
        setID = setRaw(self.eth_if, self.server_addr, protocolDict["broadcast"],
                       self.pkg_index, flowCtrlDict["setID"])
        setID.send_write_cmd(dataAddressDict["deviceID"], dataLenDict["deviceID"], str(start_id))
        self.pkg_index_addon()
        self.reset_cmd_set()

    def set_fpga_write_flash(self, fpga_id='broadcast'):
        setID = setRaw(self.eth_if, self.server_addr, protocolDict[fpga_id],
                       self.pkg_index, flowCtrlDict["writeRegister"])

        setID.send_write_cmd(dataAddressDict["flashControl"], dataLenDict["flashControl"], '128')
        self.pkg_index_addon()
        self.reset_cmd_set()

    def set_fpga_read_flash(self, fpga_id='broadcast'):
        setID = setRaw(self.eth_if, self.server_addr, protocolDict[fpga_id],
                       self.pkg_index, flowCtrlDict["writeRegister"])
        setID.send_write_cmd(dataAddressDict["flashControl"], dataLenDict["flashControl"], '64')
        self.pkg_index_addon()
        self.reset_cmd_set()

    def process_fpga_ota_finish(self, dest_fpga_id: int) -> int:
        self.lock.acquire(timeout=self.lock_time)
        start_time = None
        receive_ota_finish_ack = getRaw(self.eth_if, flowCtrlDict["otaFinish"], self.pkg_index)
        receive_ota_finish_ack.start()
        for i in range(5):
            if receive_ota_finish_ack.selector is not None:
                break
            time.sleep(self.ack_wait_time)

        process_ota_finish_raw = setRaw(self.eth_if, self.server_addr, str(dest_fpga_id),
                                        self.pkg_index, flowCtrlDict["otaFinish"])
        process_ota_finish_raw.send_ota_finish_data()
        if self.debug is True:
            start_time = time.time()
        for i in range(self.rw_max_count):
            if i > 0:
                # log.debug("write cmd read ack count : %d", i)
                pass
            time.sleep(self.ack_wait_time)
            if receive_ota_finish_ack.is_alive() == 0:
                # log.debug("already got a response from FPGA")
                break
            process_ota_finish_raw = setRaw(self.eth_if, self.server_addr, str(dest_fpga_id),
                                            self.pkg_index, flowCtrlDict["otaFinish"])
            process_ota_finish_raw.send_ota_data()
        ret = receive_ota_finish_ack.ackStatus
        receive_ota_finish_ack.set_stop(True)
        receive_ota_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()
        self.lock.release()
        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0
        else:
            return -1

    def process_fpga_ota(self, dest_fpga_id: int, b_value: bytes) -> int:
        self.lock.acquire(timeout=self.lock_time)
        start_time = None
        receive_ota_ack = getRaw(self.eth_if, flowCtrlDict["OTA_ack"], self.pkg_index)
        receive_ota_ack.start()
        for i in range(5):
            if receive_ota_ack.selector is not None:
                break
            time.sleep(self.ack_wait_time)

        process_ota_raw = setRaw(self.eth_if, self.server_addr, str(dest_fpga_id),
                                 self.pkg_index, flowCtrlDict["OTA"])
        process_ota_raw.send_ota_data(b_value)
        if self.debug is True:
            start_time = time.time()
        for i in range(self.rw_max_count):
            if i > 0:
                # log.debug("write cmd read ack count : %d", i)
                pass
            time.sleep(self.ack_wait_time)
            if receive_ota_ack.is_alive() == 0:
                # log.debug("already got a response from FPGA")
                break
            process_ota_raw = setRaw(self.eth_if, self.server_addr, str(dest_fpga_id),
                                     self.pkg_index, flowCtrlDict["OTA"])
            process_ota_raw.send_ota_data(b_value)
        ret = receive_ota_ack.ackStatus
        receive_ota_ack.set_stop(True)
        receive_ota_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()
        self.lock.release()
        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0
        else:
            return -1

    def write_fpga_register_with_bytes(self, fpga_id: int, register_name: str, value: bytes) -> int:
        if register_name in dataAddressDict.keys():
            # log.debug("going to write %s", register_name)
            pass
        else:
            log.fatal("no such register : %s", register_name)
            return -1
        # add lock
        self.lock.acquire(timeout=self.lock_time)  # 1 sec timeout ...10 * 0.1
        # must add value len compare later
        start_time = None
        receive_write_ack = getRaw(self.eth_if, flowCtrlDict["writeRegister_ack"], self.pkg_index)
        receive_write_ack.start()
        for i in range(5):
            if receive_write_ack.selector is not None:
                break
            time.sleep(self.ack_wait_time)
        # log.debug("before send, receive_read_ack.is_alive() : %d", receive_write_ack.is_alive())
        write_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                self.pkg_index, flowCtrlDict["writeRegister"])
        write_register.send_write_cmd_with_bytes(dataAddressDict[register_name], dataLenDict[register_name], value)
        if self.debug is True:
            start_time = time.time()
        for i in range(self.rw_max_count):
            if i > 0:
                # log.debug("write cmd read ack count : %d", i)
                pass
            time.sleep(self.ack_wait_time)
            if receive_write_ack.is_alive() == 0:
                # log.debug("already got a response from FPGA")
                break
            # log.debug("before send, receive_read_ack.is_alive() : %d", receive_write_ack.is_alive())
            write_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                    self.pkg_index, flowCtrlDict["writeRegister"])

            write_register.send_write_cmd_with_bytes(dataAddressDict[register_name], dataLenDict[register_name], value)

        ret = receive_write_ack.ackStatus
        receive_write_ack.set_stop(True)
        receive_write_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()
        self.lock.release()
        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0
        else:
            return -1

    def write_fpga_register(self, fpga_id: int, register_name: str, value: str) -> int:
        if register_name in dataAddressDict.keys():
            # log.debug("going to write %s", register_name)
            pass
        else:
            log.fatal("no such register : %s", register_name)
            return -1
        # add lock
        self.lock.acquire(timeout=self.lock_time)  # 1 sec timeout ...10 * 0.1
        # must add value len compare later
        start_time = None
        receive_write_ack = getRaw(self.eth_if, flowCtrlDict["writeRegister_ack"], self.pkg_index)
        receive_write_ack.start()
        for i in range(5):
            if receive_write_ack.selector is not None:
                break
            time.sleep(self.ack_wait_time)
        # log.debug("before send, receive_read_ack.is_alive() : %d", receive_write_ack.is_alive())
        write_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                self.pkg_index, flowCtrlDict["writeRegister"])
        write_register.send_write_cmd(dataAddressDict[register_name], dataLenDict[register_name], value)
        if self.debug is True:
            start_time = time.time()
        for i in range(self.rw_max_count):
            if i > 0:
                # log.debug("write cmd read ack count : %d", i)
                pass
            time.sleep(self.ack_wait_time)
            if receive_write_ack.is_alive() == 0:
                # log.debug("already got a response from FPGA")
                break
            # log.debug("before send, receive_read_ack.is_alive() : %d", receive_write_ack.is_alive())
            write_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                    self.pkg_index, flowCtrlDict["writeRegister"])

            write_register.send_write_cmd(dataAddressDict[register_name], dataLenDict[register_name], value)

        ret = receive_write_ack.ackStatus
        receive_write_ack.set_stop(True)
        receive_write_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()
        self.lock.release()
        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0
        else:
            return -1

    def read_fpga_register(self, fpga_id: int, register_name: str) -> (int, int):
        if register_name in dataAddressDict.keys():
            # log.debug("going to read %s", register_name)
            pass
        else:
            log.fatal("no such register : %s", register_name)
            return -1, None
        # add lock
        self.lock.acquire(timeout=self.lock_time)  # 1 sec timeout ...10 * 0.1
        receive_read_ack = getRaw(self.eth_if, flowCtrlDict["readRegister_ack"], self.pkg_index)
        receive_read_ack.start()
        # log.debug("before send, receive_read_ack.is_alive() : %d", receive_read_ack.is_alive())
        for i in range(5):
            if receive_read_ack.selector is not None:
                break
            time.sleep(0.01)
        read_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                               self.pkg_index, flowCtrlDict["readRegister"])

        read_register.send_read_cmd(dataAddressDict[register_name],
                                    dataLenDict[register_name],
                                    str(dataLenDict[register_name]))
        if self.debug is True:
            start_time = time.time()
        for i in range(self.rw_max_count):
            if i > 0:
                # log.debug("cmd read count : %d", i)
                pass
            time.sleep(0.01)
            # log.debug("after send, receive_read_ack.is_alive() : %d", receive_read_ack.is_alive())
            if receive_read_ack.is_alive() == 0:
                # log.debug("already got a response from FPGA")
                break

            read_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                   self.pkg_index, flowCtrlDict["readRegister"])

            read_register.send_read_cmd(dataAddressDict[register_name],
                                        dataLenDict[register_name],
                                        str(dataLenDict[register_name]))

        ret = receive_read_ack.ackStatus
        read_payload = receive_read_ack.payload
        receive_read_ack.set_stop(True)
        receive_read_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()
        self.lock.release()
        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0, read_payload
        else:
            return ret, None

    def read_fpga_register_bytes(self, fpga_id: int, register_name: str) -> (int, bytes):
        if register_name in dataAddressDict.keys():
            # log.debug("going to read %s", register_name)
            pass
        else:
            log.fatal("no such register : %s", register_name)
            return -1, None
        # add lock
        self.lock.acquire(timeout=self.lock_time)  # 1 sec timeout ...10 * 0.1
        receive_read_ack = getRaw_Bytes(self.eth_if, flowCtrlDict["readRegister_ack"], self.pkg_index)
        receive_read_ack.start()
        # log.debug("before send, receive_read_ack.is_alive() : %d", receive_read_ack.is_alive())
        for i in range(5):
            if receive_read_ack.selector is not None:
                break
            time.sleep(0.01)
        read_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                               self.pkg_index, flowCtrlDict["readRegister"])

        read_register.send_read_cmd(dataAddressDict[register_name],
                                    dataLenDict[register_name],
                                    str(dataLenDict[register_name]))
        if self.debug is True:
            start_time = time.time()
        for i in range(self.rw_max_count):
            if i > 0:
                # log.debug("cmd read count : %d", i)
                pass
            time.sleep(0.01)
            # log.debug("after send, receive_read_ack.is_alive() : %d", receive_read_ack.is_alive())
            if receive_read_ack.is_alive() == 0:
                # log.debug("already got a response from FPGA")
                break

            read_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                   self.pkg_index, flowCtrlDict["readRegister"])

            read_register.send_read_cmd(dataAddressDict[register_name],
                                        dataLenDict[register_name],
                                        str(dataLenDict[register_name]))

        ret = receive_read_ack.ackStatus
        read_payload = receive_read_ack.payload
        receive_read_ack.set_stop(True)
        receive_read_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()
        self.lock.release()
        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0, read_payload
        else:
            return ret, None
