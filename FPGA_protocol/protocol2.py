# protocol2.0 2024/02/16 by Doris
from global_def import log # import log_utils # utils.log_utils
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

#with open("dataFPGA.json", "r") as jsonFile:
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
                   "UTC" : b'\x04\x00\x00\x00',
                   "MD5" : b'\x08\x00\x00\x00',
                   "currentGammaTable" : b'\x18\x00\x00\x00',
                   "frameWidth" : b'\x19\x00\x00\x00',
                   "frameHeight" : b'\x1B\x00\x00\x00',
                   "currentGain" : b'\x1D\x00\x00\x00',
                   "panelWay" : b'\x21\x00\x00\x00',
                   "ledArrangement" : b'\x22\x00\x00\x00',
                   "gammaTable" : b'\x00\x20\x00\x00',
                   "test" : b'\x11\x22\x33\x44'}

dataLenDict = {"deviceID" : 1,
               "flashControl" : 1,
               "UTC" : 4,
               "MD5" : 16,
               "currentGammaTable" : 1,
               "frameWidth" : 2,
               "frameHeight" : 2,
               "currentGain" : 4,
               "panelWay" : 1,
               "ledArrangement" : 2,
               "gammaTable" : 98304,
               "channelSetting" : 2}

portDataAddressDict = { "numberOfPixel" : b'\x00\x03\x00\x00',
                        "startX" : b'\x00\x03\x00\x02',
                        "startY" : b'\x00\x03\x00\x04',
                        "portWidth" : b'\x00\x03\x00\x06',
                        "portHeight" : b'\x00\x03\x00\x08'}

panelWayDict = {"R_U_L_U" : '0000',
                "L_U_R_U" : '0001',
                "R_D_L_D" : '0002',
                "L_D_R_D" : '0003',
                "U_R_D_R" : '0004',
                "U_L_D_L" : '0005',
                "D_R_U_R" : '0006',
                "D_L_U_L" : '0007'}

ledArrangementDict = {"RGB" : '00',
                      "RBG" : '01',
                      "GRB" : '02',
                      "GBR" : '03',
                      "BGR" : '04',
                      "BRG" : '05'}


# set port data address
def setPort(dataAdd, channel):
    channel = int(channel) * 0x0A
    dataAdd = int.from_bytes(dataAdd, "big")
    portDataAdd = (dataAdd + channel).to_bytes(4, 'little')
    return portDataAdd
    # self.sendCMD(portDataAdd, 2, data) # len固定為2

# 設定要傳的raw data資料
class setRaw(threading.Thread):
    # 初始化各項欄位資料
    def __init__(self, interface, sourceAdd, destinationAdd, packageIndex, flowCtrl):
        threading.Thread.__init__(self)
        # OTA packageIndex = 0
        self.packageIndex = packageIndex        # 封包順序，現在用來比對是否為同一個ACK封包
        self.interface = interface              # 網路界面
        self.sourceAdd = sourceAdd              # 主控
        # self.destinationAdd = destinationAdd
        # print("destinationAdd = ", destinationAdd)
        
        # turn data type to byte
        if isinstance(destinationAdd, bytes):
            self.destinationAdd = destinationAdd
        else:
            # turn int -> hex -> byte (6 bytes)
            tempLen = '0'
            for i in range (12 - len(destinationAdd)):
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
                if (i+dataLen) > fileSize:
                    dataLen = fileSize - i
                    data = f.read(fileSize-i)
                    # data = data[::-1]    # LSB
                    dataAddLen = dataAddLen - dataLen + len(data)  # Address 4 bytes
                    data = dataAddLen.to_bytes(4, 'little') + data      # Address 4 bytes + OTA data
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
                if self.packageIndex  >= 255:
                    self.packageIndex = 0
                else:
                    self.packageIndex += 1
    
    def sendCMD(self, dataAdd, dataLen, rawDatas):
        # 長度不夠補0
        if len(rawDatas) < (dataLen*2):
            zero = (dataLen*2) - len(rawDatas)
            # rawDatas = rawDatas + bytearray(zero)
            rawDatas = zero * '0' + rawDatas
            # print('rawDatas + bytearray(zero) = ', rawDatas)
        
        rawDatas = int(rawDatas).to_bytes(dataLen, 'little')    # str -> byte, LSB 
        # rawDatas = bytearray.fromhex(rawDatas)[::-1]    # str -> byte, LSB 
        #print('rawDatas = ', rawDatas)
        rawData = dataAdd + rawDatas
        
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
                                self.numberOfDataByte, # number of data byte
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

    def set_stop(self, status: bool):
        self.stopThreads = status

    def run(self):
        try:
            with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as server_socket:
                # Bind the interface
                server_socket.bind((self.interface, 0))
                with selectors.DefaultSelector() as selector:

                    # Resister the socket for selection, monitoring it for I/O events
                    selector.register(server_socket.fileno(), selectors.EVENT_READ)
                    while True:
                        if self.stopThreads:
                            print("break.")
                            break
                        # Wait until the socket become readable
                        ready = selector.select()
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
                                    self.ackStatus = 0
                                    if fc == self.flowCtrl and packageIndex == self.packageIndex:
                                        if self.flowCtrl == flowCtrlDict["readRegister_ack"]:
                                            # Extract a payload
                                            self.payload = frame[17:17+dataLen-1]
                                            self.payload = int.from_bytes(self.payload, "little")
                                    return
                                elif ack == b'\x01':
                                    log.debug("CRC Error")
                                    self.ackStatus = -1
                                    return
                                elif ack == b'\x02':
                                    log.debug("Data Length Error")
                                    self.ackStatus = -1
                                    return
                                else:
                                    log.debug("ACK response Error")
                                    self.ackStatus = -1
                                    return
        except Exception as e:
            log.fatal(e)


class FPGACmdCenter:
    def __init__(self, interface, server_addr, read_timeout=5, debug=True):
        self.eth_if = interface
        self.write_cmd = None
        self.read_cmd = None
        self.pkg_index = 0  # from 0
        self.server_addr = server_addr
        self.read_timeout = read_timeout
        self.debug = debug

    def reset_cmd_set(self):
        self.write_cmd = None
        self.read_cmd = None

    def pkg_index_addon(self):
        if self.pkg_index > 0xff:
            self.pkg_index = 0
        self.pkg_index += 1

    ''' '''
    def set_fpga_id_broadcast(self, start_id: int):
        setID = setRaw(self.eth_if, self.server_addr, protocolDict["broadcast"],
                       self.pkg_index, flowCtrlDict["setID"])
        setID.sendCMD(dataAddressDict["deviceID"], dataLenDict["deviceID"], str(start_id))
        self.pkg_index_addon()
        self.reset_cmd_set()

    def write_fpga_register(self, fpga_id: int, register_name: str, value: str) -> int:
        if register_name in dataAddressDict.keys():
            log.debug("going to write %s", register_name)
        else:
            log.fatal("no such register : %s", register_name)
            return -1
        # must add value len compare later

        receive_write_ack = getRaw(self.eth_if, flowCtrlDict["writeRegister_ack"], self.pkg_index)
        receive_write_ack.start()

        time.sleep(0.5)
        if self.debug is True:
            start_time = time.time()
        for i in range(5):
            log.debug("read ack count : %d", i)
            log.debug("before send, receive_read_ack.is_alive() : %d", receive_write_ack.is_alive())
            write_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                    self.pkg_index, flowCtrlDict["writeRegister"])
            write_register.sendCMD(dataAddressDict[register_name], dataLenDict[register_name], value)
            time.sleep(0.1)
            if receive_write_ack.is_alive() == 0:
                log.debug("already got a response from FPGA")
                break

        ret = receive_write_ack.ackStatus
        receive_write_ack.set_stop(True)
        receive_write_ack = None

        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)
        if ret == 0:
            return 0
        else:
            return -1

    def read_fpga_register(self, fpga_id: int, register_name: str) -> (int, bytes):
        if register_name in dataAddressDict.keys():
            log.debug("going to read %s", register_name)
        else:
            log.fatal("no such register : %s", register_name)
            return -1, None

        receive_read_ack = getRaw(self.eth_if, flowCtrlDict["readRegister_ack"], self.pkg_index)
        receive_read_ack.start()
        time.sleep(0.5)
        if self.debug is True:
            start_time = time.time()
        for i in range(5):
            log.debug("read count : %d", i)
            log.debug("before send, receive_read_ack.is_alive() : %d", receive_read_ack.is_alive())
            read_register = setRaw(self.eth_if, self.server_addr, str(fpga_id),
                                   self.pkg_index, flowCtrlDict["readRegister"])
            read_register.sendCMD(dataAddressDict[register_name], dataLenDict[register_name],
                                  str(dataLenDict[register_name]))
            time.sleep(0.1)
            log.debug("after send, receive_read_ack.is_alive() : %d", receive_read_ack.is_alive())
            if receive_read_ack.is_alive() == 0:
                log.debug("already got a response from FPGA")
                break

        ret = receive_read_ack.ackStatus
        read_payload = receive_read_ack.payload
        receive_read_ack.set_stop(True)
        receive_read_ack = None
        self.pkg_index_addon()
        self.reset_cmd_set()

        if self.debug is True:
            diff = time.time() - start_time
            log.debug("time diff = %d", diff)

        if ret == 0:
            return 0, read_payload
        else:
            return ret, None






def setFPGAid(id):
    # send CMD to set ID ; broadcast no ack
    setID = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], protocolDict["broadcast"], 0, flowCtrlDict["setID"])
    setID.sendCMD(dataAddressDict["deviceID"], dataLenDict["deviceID"], id)
    # 固化 set ID data
    # writeRegister = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], protocolDict["broadcast"], 0, flowCtrlDict["writeRegister"])
    # writeRegister.sendCMD(dataAddressDict["flashControl"], dataLenDict["flashControl"], '128')

def readFPGA(id, n, dataName):
    pkIndex = random.randint(0, 99)
    receiveReadACK = getRaw(protocolDict["interface"], flowCtrlDict["readRegister_ack"], pkIndex)
    stopThreads = False
    #print("random = ", pkIndex)

    receiveReadACK.start()
    time.sleep(0.5)
    startTime = time.time()
    while True:
        readRegister = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], id, pkIndex, flowCtrlDict["readRegister"])
        readRegister.sendCMD(dataAddressDict[dataName], dataLenDict[dataName], str(dataLenDict[dataName]))
        time.sleep(0.5)
        if receiveReadACK.ackStatus == 0:
            #print("receiveReadACK.payload = ", receiveReadACK.payload)
            #data[dataName] = str(receiveReadACK.payload)
            '''
            data["fpgaID"].append({
                dataName: str(receiveReadACK.payload)
            })
            '''
            data["fpgaID"][n][dataName] = str(receiveReadACK.payload)
            stopThreads = True
            #print('receiveReadACK = ', receiveReadACK.is_alive())
            receiveReadACK.join()
            break
        endTime = time.time()
        if (endTime - startTime) >= 1:
            global stop
            stop = True
            print('cannot receive any ACK')
            return