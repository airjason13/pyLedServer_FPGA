from global_def import log # Jason for merge to main app @20240306
import socket
import selectors
import struct
import binascii
import threading
import time
import os
import gammaTable

from ethernet import *

# log = log_utils.logging_init(__file__) # utils.log_utils.logging_init(__file__)

protocolDict = {"preamble": b'\x55\x55\x55\x55\x55\x55\x55',
                "sof": b'\xD5',
                "interface": 'eno2',
                "broadcast": b'\x00\x00\x00\x00\x00\x00',
                "sourceAddress": b'\x00\x00\x00\x00\x00\x01',
                "destinationAddress": b'\x00\x00\x00\x00\x00\x20',
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
                   "gammaTable": b'\x00\x20\x00\x00',
                   "test": b'\x11\x22\x33\x44'}

portDataAddressDict = {"numberOfPixel": b'\x00\x03\x00\x00',
                       "startX": b'\x00\x03\x00\x02',
                       "startY": b'\x00\x03\x00\x04',
                       "portWidth": b'\x00\x03\x00\x06',
                       "portHeight": b'\x00\x03\x00\x08'}

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


# 設定要傳的raw data資料
class setRaw(threading.Thread):
    # 初始化各項欄位資料
    def __init__(self, interface, sourceAdd, destinationAdd, flowCtrl):
        threading.Thread.__init__(self)
        self.packageIndex = 0  # 封包順序
        self.interface = interface  # 網路界面
        self.sourceAdd = sourceAdd  # 主控
        self.destinationAdd = destinationAdd
        self.flowCtrl = flowCtrl
        self.numberOfDataByte = 0

    # set port data address
    def setPort(self, dataAdd, channel, data):
        channel = int(channel) * 0x0A
        dataAdd = int.from_bytes(dataAdd, "big")
        portDataAdd = (dataAdd + channel).to_bytes(4, 'little')
        self.setData(portDataAdd, data)
        '''
        print('dataAdd : ', dataAdd)
        print('type of dataAdd = ', type(dataAdd))
        print('type of channel = ', type(channel))
        print('portDataAdd : ', portDataAdd)
        '''

    def setData(self, dataAdd, rawDatas):
        if self.flowCtrl == flowCtrlDict["OTA"]:  # OTA = b'\x11'
            dataLen = ETH_DATA_LEN - ETH_TLEN * 5  # ETH_DATA_LEN = 1500, ETH_TLEN = 2, 2 byte
            dataAddLen = 0  # 2 byte
            log.debug('file: %s', rawDatas)
            with open(rawDatas, 'rb') as f:
                fileSize = os.path.getsize(rawDatas)
                log.debug('fileSize = %d', fileSize)
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
        else:  # 傳CMD
            if len(rawDatas) % 2 == 1:
                log.debug('rawDatas = %d', len(rawDatas))
                rawDatas = rawDatas + '0'  # 輸入奇數個數字，最後一個補0
            # print('size of rawDatas = ', len(rawDatas))
            # print('type of rawDatas = ', type(rawDatas))    # <class 'str'>
            rawDatas = bytearray.fromhex(rawDatas)[::-1]  # LSB 逆序?出,???出所有字符串 [::-1]
            print('rawDatas = ', rawDatas)
            # print('type of rawDatas = ', type(rawDatas))    # <class 'bytearray'>
            # rawData = binascii.unhexlify(rawDatas) # byte to ascii(?)
            rawData = dataAdd + rawDatas
            # print('rawData = ', rawData)
            # print('type of rawData = ', type(rawData))  # <class 'bytes'>
            self.numberOfDataByte = len(rawData)
            self.sendSocket(rawData)

    def sendSocket(self, rawData):
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


# 攔截ACK封包
class receiveSocket(threading.Thread):
    def __init__(self, interface):
        threading.Thread.__init__(self)
        self.interface = interface
        print('receiveSocket __init__')

    def run(self):
        with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as server_socket:
            # Bind the interface
            server_socket.bind((self.interface, 0))
            with selectors.DefaultSelector() as selector:
                # Resister the socket for selection, monitoring it for I/O events
                selector.register(server_socket.fileno(), selectors.EVENT_READ)
                while True:
                    if stopThreads:
                        log.debug("receiveSocket thread break.")
                        break
                    # Wait until the socket become readable
                    ready = selector.select()
                    if ready:
                        # Receive a frame, ETH_FRAME_LEN = 1514
                        frame = server_socket.recv(ETH_FRAME_LEN)
                        # Extract a header, ETH_HLEN = 14
                        header = frame[:16]
                        # Unpack an Ethernet header in network byte order
                        dst, src, index, number, fc = struct.unpack('!6s6ss2ss', header)
                        dataLen = int.from_bytes(number, "big")
                        # Extract a payload
                        payload = frame[16:16 + dataLen]
                        # number, fc = struct.unpack('!2ss', payload)

                        # ETH_DATA_LEN = 1500	
                        '''
                        if dst == protocolDict["destinationAddress"]:
                            print(f'Destination Address: {bytes_to_eui48(dst)}, \n'
                                  f'Source Address: {bytes_to_eui48(src)}, \n'
                                  f'Package Index: {int.from_bytes(index, "big")}, \n'
                                  f'Number of Data Byte: {int.from_bytes(number, "big")}, \n'
                                  # f'payload: {payload[:ETH_DATA_LEN]}...')
                                  f'Flow Ctrl: {fc}, \n'
                                  f'Data: {payload}')
                        '''

                log.debug("Done.")




if __name__ == '__main__':
    '''
    receiveRaw = receiveSocket('eno2')
    stopThreads = False #receiveSocket
    receiveRaw.start()
    time.sleep(2)
    # interface, destinationAdd, flowCtrl, rawData, eth0
    setRawID = setRaw('eno2', b'\xff\xff\xff\xff\xff\xff', b'\x10')     #Set ID
    setRawID.setData('1122334420')
    
    setRawOTA = setRaw('eno2', b'\x00\x00\x00\x00\x00\x20', b'\x11')    #OTA
    setRawOTA.setData('cmdPy.zip')  #spi_x4.mcs cmdPy.zip
    
    stopThreads = True
    receiveRaw.join()
    '''

    # interface, sourceAdd, destinationAdd, flowCtrl

    receiveACK = receiveSocket(protocolDict["interface"])
    stopThreads = False
    receiveACK.start()
    print('receiveACK start = ', receiveACK.is_alive())
    # print('gammaTable = ', bytearray.fromhex(gammaTable.gammaTable())[:])
    '''
    setRawID = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], protocolDict["broadcast"], flowCtrlDict["setID"])
    setRawID.setData(dataAddressDict["test"], '20')
    '''
    writeRegister = setRaw(protocolDict["interface"], protocolDict["sourceAddress"],
                           protocolDict["destinationAddress"], flowCtrlDict["writeRegister"])
    writeRegister.setPort(portDataAddressDict["numberOfPixel"], '5', '960')
    # setPort(dataAdd, channel, data)
    # writeRegister.setPort(portDataAddressDict["numberOfPixel"], 5)
    # writeRegister.setData(dataAddressDict["flashControl"], '40')
    # writeRegister.setData(dataAddressDict["currentGain"], '00000000')
    '''
    writeRegister.setData(b'\x00\x20\x00\x00', gammaTable.gammaTable())
    writeRegister.setData(b'\x00\x22\x00\x00', gammaTable.gammaTable())
    writeRegister.setData(b'\x00\x24\x00\x00', gammaTable.gammaTable())
    '''
    '''
    writeRegister.setData(dataAddressDict["currentGammaTable"], '01')
    writeRegister.setData(dataAddressDict["currentGammaTable"], '00')
    '''

    # writeRegister = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], protocolDict["destinationAddress"], flowCtrlDict["writeRegister"])
    '''
    writeRegister.setData(dataAddressDict["panelWay"], '00')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '01')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '02')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '03')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '04')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '05')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '06')
    time.sleep(5)
    writeRegister.setData(dataAddressDict["panelWay"], '07')
    time.sleep(5)
    '''
    # writeRegister.setData(dataAddressDict["panelWay"], '00')

    # writeRegister.setData(dataAddressDict["panelWay"], panelWayDict["L_D_R_D"])
    # writeRegister.setData(dataAddressDict["UTC"], 'a6a5a4a3a2a1')
    writeRegister.setData(dataAddressDict["frameWidth"], '01E0')  # 轉成16進位
    writeRegister.setData(dataAddressDict["frameHeight"], '02D0')

    # readRegister = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], protocolDict["destinationAddress"], flowCtrlDict["readRegister"])
    # readRegister.setData(dataAddressDict["currentGammaTable"], '00')
    # readRegister.setData(dataAddressDict["UTC"], '0006')

    '''
    setRawOTA = setRaw(protocolDict["interface"], protocolDict["sourceAddress"], protocolDict["destinationAddress"], flowCtrlDict["OTA"])    #OTA
    setRawOTA.setData(dataAddressDict["test"], '1229.bit')
    '''
    stopThreads = True
    receiveACK.join(5)
    # time.sleep(2)
    print('receiveACK stopThreads = ', receiveACK.is_alive())
