from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QFileSystemWatcher
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton
from global_def import *
from FPGA_protocol.protocol2 import *
from media_engine.media_engine import MediaEngine
# from ext_qt_widgets.system_file_watcher import FileWatcher

import threading
import binascii
import socket
import struct
import json
import os

class LedSettingsPage(QWidget):
    # need to change to Jason function
    signal_file_changed = pyqtSignal(str)

    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, fpga_list: [], **kwargs):
        super(LedSettingsPage, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.name = _name
        self.nw = None

        # watch if json file change
        # need to change to Jason function
        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(os.getcwd() + '/led_config/dataFPGA.json')
        self.watcher.fileChanged.connect(self.file_changed)
        # print("os.getcwd() = ", os.getcwd())

        list = ["deviceID", "portNumber", "portWay", "portStyle", "startX", "startY", "portWidth", "portHeight",
                "frameWidth", "frameHeight"]  # 10
        value = []
        # read data from FPGA
        readFPGA = FPGACmdCenter(ETH_DEV, protocolDict["sourceAddress"])
        id = 2
        self.fpgaLen = 0
        while True:
            ret, str_value = readFPGA.read_fpga_register(id, "deviceID")
            print("str_value = ", str_value)
            if str_value == None:
                break

            tempVal = []
            tempVal = tempVal + [str(id), "0", "0"]
            ret, str_value = readFPGA.read_fpga_register(id, "panelWay")
            tempVal = tempVal + [str(str_value)]
            ret, str_value = readFPGA.read_fpga_register(id, 'startX_p{}'.format("0"))  # only read 0 port
            tempVal = tempVal + [str(str_value)]
            ret, str_value = readFPGA.read_fpga_register(id, 'startY_p{}'.format("0"))  # only read 0 port
            tempVal = tempVal + [str(str_value)]
            ret, str_value = readFPGA.read_fpga_register(id, 'portWidth_p{}'.format("0"))  # only read 0 port
            tempVal = tempVal + [str(str_value)]
            ret, str_value = readFPGA.read_fpga_register(id, 'portHeight_p{}'.format("0"))  # only read 0 port
            tempVal = tempVal + [str(str_value)]
            ret, str_value = readFPGA.read_fpga_register(id, "frameWidth")
            tempVal = tempVal + [str(str_value)]
            ret, str_value = readFPGA.read_fpga_register(id, "frameHeight")
            tempVal = tempVal + [str(str_value)]
            value.append(tempVal)

            # print(value)
            id = id + 1
            self.fpgaLen = self.fpgaLen + 1

        dataJson = {"fpgaID": [dict(zip(list, row)) for row in value]}
        with open("led_config/dataFPGA.json", "w") as jsonFile:
            json.dump(dataJson, jsonFile, indent=2)
            # print('write json')

        # print("fpgaLen = ", self.fpgaLen)

        with open("led_config/dataFPGA.json", "r") as jsonFile:
            self.data = json.load(jsonFile)
            self.init_ui()

    def init_ui(self):
        ledWidthLabel = QtWidgets.QLabel('LED Width : ')
        self.ledWidthInput = QtWidgets.QLineEdit(self)
        self.ledWidthInput.setAlignment(QtCore.Qt.AlignCenter)
        # self.ledWidthInput.setPlaceholderText(data["frameWidth"])
        ledHeightLabel = QtWidgets.QLabel('   LED Height : ')
        self.ledHeightInput = QtWidgets.QLineEdit(self)
        self.ledHeightInput.setAlignment(QtCore.Qt.AlignCenter)
        # self.ledHeightInput.setPlaceholderText(data["frameHeight"])
        setBtn = QtWidgets.QPushButton('  Set  ')  # 建立按鈕
        writeFlashBtn = QtWidgets.QPushButton('  Write Flash  ')  # 建立按鈕

        box = QtWidgets.QWidget(self)  # 建立放置 QFormLayout 的 Widget
        box.setGeometry(50, 0, 1100, 150)

        layout = QtWidgets.QHBoxLayout(box)
        layout.addWidget(ledWidthLabel)
        layout.addWidget(self.ledWidthInput)
        layout.addWidget(ledHeightLabel)
        layout.addWidget(self.ledHeightInput)
        layout.addWidget(setBtn)
        layout.addWidget(writeFlashBtn)

        boxG = QtWidgets.QWidget(self)  # 建立放 QGridLayout 的元件
        boxG.setGeometry(50, 200, 1100, 700)  # 指定大小位置

        groupBox = QtWidgets.QGroupBox('FPGA Port Style')
        grid = QtWidgets.QGridLayout()  # 建立 QGridLayout

        self.portStyleList = []
        self.portImgList = []

        # if (len(data["fpgaID"]) < self.fpgaLen):
        #     self.setDefaultJson()

        for n in range(self.fpgaLen):
            portStyleLabel = QtWidgets.QLabel('FPGA ID = ' + self.data["fpgaID"][n]["deviceID"] + '\t')
            portStyleSet = QtWidgets.QLabel(
                'Start( x , y ) = ( ' + self.data["fpgaID"][n]["startX"] + ' , ' + self.data["fpgaID"][n]["startY"] + ' )' +
                '\nW x H = ' + self.data["fpgaID"][n]["portWidth"] + ' x ' + self.data["fpgaID"][n]["portHeight"]
            )
            self.portStyleList.append(portStyleSet)

            portImg = QtWidgets.QLabel(self)
            img = QtGui.QImage('materials/' + str(self.data["fpgaID"][n]["portStyle"]) + '.png')  # 讀取圖片
            portImg.setPixmap(QtGui.QPixmap(img).scaled(150, 150))  # 加入圖片
            self.portImgList.append(portImg)

            portStyleBtn = QtWidgets.QPushButton('Edit')
            portStyleBtn.setObjectName(str(n))

            grid.addWidget(portStyleLabel, n, 0)
            grid.addWidget(portImg, n, 1)
            grid.addWidget(portStyleSet, n, 2)
            grid.addWidget(portStyleBtn, n, 3)

            portStyleBtn.clicked.connect(self.fpgaEdit)

            portStyleBtn.setStyleSheet('''
                QPushButton{
                    background-color: none;
                    border: none;
                    color: #FFFFBB;
                    font-size: 30px;
                    font-weight: bold;
                }
                QPushButton:hover{
                    color: #888888;
                }
            ''')

            portStyleLabel.setStyleSheet('''
                QLabel{
                    color: #EEEEEE;
                    font-size: 30px;
                    font-weight: bold;
                }
            ''')

            portStyleSet.setStyleSheet('''
                QLabel{
                    color: #EEEEEE;
                    font-size: 30px;
                    font-weight: bold;
                }
            ''')

        groupBox.setLayout(grid)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)

        layoutS = QtWidgets.QVBoxLayout(boxG)
        layoutS.addWidget(scroll)

        self.ledWidthInput.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;
        ''')
        self.ledHeightInput.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;
        ''')
        ledWidthLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 40px;
            font-weight: bold;
        ''')
        ledHeightLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 40px;
            font-weight: bold;
        ''')
        setBtn.setStyleSheet('''
            QPushButton{
                background-color: none;
                border: none;
                color: #FFFFBB;
                font-size: 30px;
                font-weight: bold;
            }
            QPushButton:hover{
                color: #888888;
            }
        ''')
        writeFlashBtn.setStyleSheet('''
            QPushButton{
                background-color: none;
                border: none;
                color: #FFCCCC;
                font-size: 30px;
                font-weight: bold;
            }
            QPushButton:hover{
                color: #888888;
            }
        ''')

        setBtn.clicked.connect(self.setWidthHeight)
        writeFlashBtn.clicked.connect(self.writeFlash)

    # 固化
    def writeFlash(self):
        writePortStyle = FPGACmdCenter(ETH_DEV, protocolDict["sourceAddress"])
        writePortStyle.set_fpga_write_flash()

    def setDefaultJson(self):
        for i in range(len(self.data["fpgaID"]), self.fpgaLen):
            data["fpgaID"][i]["deviceID"] = str(i)
            data["fpgaID"][i]["portNumber"] = "0"
            data["fpgaID"][i]["portWay"] = 0
            data["fpgaID"][i]["portStyle"] = "0"
            data["fpgaID"][i]["startX"] = "0"
            data["fpgaID"][i]["startY"] = "0"
            data["fpgaID"][i]["portWidth"] = "0"
            data["fpgaID"][i]["portHeight"] = "0"
            data["fpgaID"][i]["frameWidth"] = "0"
            data["fpgaID"][i]["frameHeight"] = "0"

        with open("led_config/dataFPGA.json", "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)
            print('write json')

    # set the first page LED Width and Height with every port
    def setWidthHeight(self):
        print('setWidthHeight~')
        frameWidth = self.data["fpgaID"][0]["frameWidth"]
        frameHeight = self.data["fpgaID"][0]["frameHeight"]
        writeWidthHeight = FPGACmdCenter(ETH_DEV, protocolDict["sourceAddress"])

        writeData = False
        if self.ledWidthInput.text() != "":
            # self.ledWidthInput.setPlaceholderText(self.ledWidthInput.text())
            # set on RPI
            self.data["frameWidth"] = self.ledWidthInput.text()
            frameWidth = self.ledWidthInput.text()
            writeData = True
        if self.ledHeightInput.text() != "":
            # self.ledHeightInput.setPlaceholderText(self.ledHeightInput.text())
            self.data["frameHeight"] = self.ledHeightInput.text()
            frameHeight = self.ledHeightInput.text()
            writeData = True

        for i in range(self.fpgaLen):
            self.data["fpgaID"][i]["frameWidth"] = frameWidth
            self.data["fpgaID"][i]["frameHeight"] = frameHeight
            writeWidthHeight.write_fpga_register(self.data["fpgaID"][i]["deviceID"], "frameWidth",
                                                 frameWidth)
            writeWidthHeight.write_fpga_register(self.data["fpgaID"][i]["deviceID"], "frameHeight",
                                                 frameHeight)
            print(i)

        # 固化
        # writeWidthHeight.set_fpga_write_flash()

        if writeData:
            with open("led_config/dataFPGA.json", "w") as jsonFile:
                json.dump(self.data, jsonFile, indent=2)
                print('write json')


    def fpgaEdit(self):
        sender = self.sender()
        pushButton = self.findChild(QtWidgets.QPushButton, sender.objectName())
        fpgaEditID = pushButton.objectName()
        print('fpgaEdit = ', fpgaEditID)

        if self.nw is None or self.nw.close():
            self.nw = portSettingWindow(fpgaEditID)  # 連接新視窗
            self.nw.show()  # 顯示新視窗
            x = self.nw.pos().x()  # 取得新視窗目前 x 座標
            y = self.nw.pos().y()  # 取得新視窗目前 y 座標
            self.nw.move(x + 100, y + 100)  # 移動新視窗位置
        else:
            self.nw.close()
            self.nw = None

    def file_changed(self, path):
        self.signal_file_changed.emit(path)
        # print('file_changed')
        # print('self.portStyleList = ', self.portStyleList)
        with open("led_config/dataFPGA.json", "r") as jsonFile:
            self.data = json.load(jsonFile)

        for n in range(self.fpgaLen):
            self.portStyleList[n].setText(
                'Start( x , y ) = ( ' + self.data["fpgaID"][n]["startX"] + ' , ' + self.data["fpgaID"][n]["startY"] + ' )' +
                '\nW x H = ' + self.data["fpgaID"][n]["portWidth"] + ' x ' + self.data["fpgaID"][n]["portHeight"]
            )
            # self.portStyleSet.setObjectName('portStyle'+str(n))
            img = QtGui.QImage('materials/' + self.data["fpgaID"][n]["portStyle"] + '.png')
            self.portImgList[n].setPixmap(QtGui.QPixmap(img).scaled(150, 150))  # 加入圖片

    def func_test_btn(self):
        log.debug("func test btn clicked")


class portSettingWindow(QtWidgets.QWidget):
    def __init__(self, fpgaEditID):
        super().__init__()
        self.setWindowTitle('Port Setting')
        self.setStyleSheet("background-color: #222222;")
        self.resize(1500, 900)
        self.writeData = False
        # self.portStyleNum = int(data["fpgaID"][fpgaEditID]["portStyle"])
        with open("led_config/dataFPGA.json", "r") as jsonFile:
            self.data = json.load(jsonFile)
            self.ui(fpgaEditID)

    def ui(self, fpgaEditID):

        fpgaEditID = int(fpgaEditID)
        fpgaIDLabel = QtWidgets.QLabel('FPGA ID = ' + self.data["fpgaID"][fpgaEditID]["deviceID"])
        # print('FPGA fpgaEditID = ', fpgaEditID)
        currentLabel = QtWidgets.QLabel('Current Port Style  ⇨  ')
        self.portStyleImg = QtWidgets.QLabel(self)
        img = QtGui.QImage('materials/' + self.data["fpgaID"][fpgaEditID]["portStyle"] + '.png')  # 讀取圖片
        self.portStyleImg.setPixmap(QtGui.QPixmap(img).scaled(150, 150))  # 加入圖片

        setPortLabel = QtWidgets.QLabel('Port Number =  ')
        self.portInput = QtWidgets.QLineEdit(self)
        self.portInput.setMaxLength(2)
        # self.portInput.setPlaceholderText(data["fpgaID"][fpgaEditID]["portNumber"])
        self.portInput.setAlignment(QtCore.Qt.AlignCenter)
        setLabel = QtWidgets.QLabel(' , way = ')
        self.Bbox = QtWidgets.QComboBox(self)
        self.Bbox.addItems([' ⬆ ', ' ⬇ ', ' ⬅ ', ' ⮕ '])
        # self.Bbox.addItems([' up ', ' down ', ' left ', ' right '])
        self.Bbox.setCurrentIndex(int(self.data["fpgaID"][fpgaEditID]["portWay"]))
        reverseLabel = QtWidgets.QLabel(' , reverse = ')
        self.reverseInput = QtWidgets.QLineEdit(self)
        self.reverseInput.setPlaceholderText("0")
        self.reverseInput.setMaxLength(2)
        self.reverseInput.setAlignment(QtCore.Qt.AlignCenter)
        # self.rb_a = QtWidgets.QRadioButton(self)
        # self.rb_a.setText('True')
        # self.rb_b = QtWidgets.QRadioButton(self)
        # self.rb_b.setText('False')
        # self.group = QtWidgets.QButtonGroup(self)
        # self.group.addButton(self.rb_a, 1)
        # self.group.addButton(self.rb_b, 0)
        # self.Bbox.resize(100,150)

        # self.Bbox.currentIndexChanged.connect(self.showMsg)

        XYLabel1 = QtWidgets.QLabel('Start ( X , Y ) = ( ')
        self.XYInput1 = QtWidgets.QLineEdit(self)
        self.XYInput1.setAlignment(QtCore.Qt.AlignCenter)
        self.XYInput1.setPlaceholderText(self.data["fpgaID"][fpgaEditID]["startX"])
        XYLabel3 = QtWidgets.QLabel(' , ')
        self.XYInput2 = QtWidgets.QLineEdit(self)
        self.XYInput2.setAlignment(QtCore.Qt.AlignCenter)
        self.XYInput2.setPlaceholderText(self.data["fpgaID"][fpgaEditID]["startY"])
        XYLabel2 = QtWidgets.QLabel(' )\t')

        WHLabel1 = QtWidgets.QLabel('Width , Height = ( ')
        self.WHInput1 = QtWidgets.QLineEdit(self)
        self.WHInput1.setAlignment(QtCore.Qt.AlignCenter)
        self.WHInput1.setPlaceholderText(self.data["fpgaID"][fpgaEditID]["portWidth"])
        WHLabel2 = QtWidgets.QLabel(' , ')
        self.WHInput2 = QtWidgets.QLineEdit(self)
        self.WHInput2.setAlignment(QtCore.Qt.AlignCenter)
        self.WHInput2.setPlaceholderText(self.data["fpgaID"][fpgaEditID]["portHeight"])
        WHLabel3 = QtWidgets.QLabel(' )\t')

        cancelBtn = QtWidgets.QPushButton('  Cancel  ')  # 建立按鈕
        setBtn = QtWidgets.QPushButton('  Set  ')  # 建立按鈕
        cancelBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        setBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        setBtn.clicked.connect(lambda: self.tempData(fpgaEditID))
        cancelBtn.clicked.connect(self.cancel)

        fpgaIDLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        currentLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        setPortLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        setLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        XYLabel1.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        XYLabel2.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        XYLabel3.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        WHLabel1.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        WHLabel2.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        WHLabel3.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        self.portInput.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;
        ''')

        self.XYInput1.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;
        ''')

        self.XYInput2.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;

        ''')

        self.WHInput1.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;

        ''')

        self.WHInput2.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;

        ''')

        self.Bbox.setStyleSheet('''
            border: 3px solid #FFFFBB;
            border-radius: 5px;
            color: #FFFFBB;
            font-size: 30px;
            font-weight: bold;
            width: 80px;
        ''')

        reverseLabel.setStyleSheet('''
            color: #FFFFFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        self.reverseInput.setStyleSheet('''
            border: 3px hidden;
            border-bottom: 3px solid #FFFFFF;
            color: #FFFFBB;
            font-size: 40px;
            font-weight: bold;
        ''')

        # self.rb_b.setStyleSheet('''
        #     color: #FFFFFF;
        #     font-size: 25px;
        #     font-weight: bold;
        # ''')
        #
        # self.rb_a.setStyleSheet('''
        #     color: #FFFFFF;
        #     font-size: 25px;
        #     font-weight: bold;
        # ''')

        setBtn.setStyleSheet('''
            background-color: none;
            border: 3px solid #CCEEFF;
            border-radius: 10px;
            color: #CCEEFF;
            font-size: 30px;
            font-weight: bold;
        ''')

        cancelBtn.setStyleSheet('''
            background-color: none;
            border: 3px solid #FFB7DD;
            border-radius: 10px;
            color: #FFB7DD;
            font-size: 30px;
            font-weight: bold;
        ''')

        self.button0 = QtWidgets.QPushButton()
        self.button0.setStyleSheet('''
            border-image: url(materials/0.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button1 = QtWidgets.QPushButton()
        self.button1.setStyleSheet('''
            border-image: url(materials/1.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button2 = QtWidgets.QPushButton()
        self.button2.setStyleSheet('''
            border-image: url(materials/2.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button3 = QtWidgets.QPushButton()
        self.button3.setStyleSheet('''
            border-image: url(materials/3.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button4 = QtWidgets.QPushButton()
        self.button4.setStyleSheet('''
            border-image: url(materials/4.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button5 = QtWidgets.QPushButton()
        self.button5.setStyleSheet('''
            border-image: url(materials/5.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button6 = QtWidgets.QPushButton()
        self.button6.setStyleSheet('''
            border-image: url(materials/6.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')
        self.button7 = QtWidgets.QPushButton()
        self.button7.setStyleSheet('''
            border-image: url(materials/7.png) 0 0 0 0 stretch stretch;
            background-repeat: no-repeat;
            height: 150px;
        ''')

        self.button0.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button3.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button4.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button5.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button6.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.button7.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.button0.clicked.connect(lambda: self.portStyle('0', fpgaEditID))
        self.button1.clicked.connect(lambda: self.portStyle('1', fpgaEditID))
        self.button2.clicked.connect(lambda: self.portStyle('2', fpgaEditID))
        self.button3.clicked.connect(lambda: self.portStyle('3', fpgaEditID))
        self.button4.clicked.connect(lambda: self.portStyle('4', fpgaEditID))
        self.button5.clicked.connect(lambda: self.portStyle('5', fpgaEditID))
        self.button6.clicked.connect(lambda: self.portStyle('6', fpgaEditID))
        self.button7.clicked.connect(lambda: self.portStyle('7', fpgaEditID))

        Lbox = QtWidgets.QWidget(self)  # 建立放置 QFormLayout 的 Widget
        Lbox.setGeometry(50, 0, 250, 100)
        Llayout = QtWidgets.QVBoxLayout(Lbox)
        Llayout.addWidget(fpgaIDLabel)

        Cbox = QtWidgets.QWidget(self)
        Cbox.setGeometry(450, 0, 800, 200)
        Clayout = QtWidgets.QHBoxLayout(Cbox)
        Clayout.addWidget(currentLabel)
        Clayout.addWidget(self.portStyleImg)

        Sbox = QtWidgets.QWidget(self)
        Sbox.setGeometry(450, 200, 750, 150)
        Slayout = QtWidgets.QHBoxLayout(Sbox)
        Slayout.addWidget(setPortLabel)
        Slayout.addWidget(self.portInput)
        Slayout.addWidget(setLabel)
        Slayout.addWidget(self.Bbox)
        Slayout.addWidget(reverseLabel)
        Slayout.addWidget(self.reverseInput)
        # Slayout.addWidget(self.rb_a)
        # Slayout.addWidget(self.rb_b)

        # Bbox = QtWidgets.QComboBox(self)
        # Bbox.addItems(['⬆','⬇','⬅','⮕'])
        # Bbox.setGeometry(1250,260,90,35)
        # Bbox.currentIndexChanged.connect(self.showMsg)

        XYbox = QtWidgets.QWidget(self)
        XYbox.setGeometry(450, 350, 850, 150)
        Slayout = QtWidgets.QHBoxLayout(XYbox)
        Slayout.addWidget(XYLabel1)
        Slayout.addWidget(self.XYInput1)
        Slayout.addWidget(XYLabel3)
        Slayout.addWidget(self.XYInput2)
        Slayout.addWidget(XYLabel2)
        # Slayout.addWidget(XYBtn)

        WHbox = QtWidgets.QWidget(self)
        WHbox.setGeometry(450, 500, 900, 150)
        Slayout = QtWidgets.QHBoxLayout(WHbox)
        Slayout.addWidget(WHLabel1)
        Slayout.addWidget(self.WHInput1)
        Slayout.addWidget(WHLabel2)
        Slayout.addWidget(self.WHInput2)
        Slayout.addWidget(WHLabel3)

        Setbox = QtWidgets.QWidget(self)
        Setbox.setGeometry(1100, 650, 300, 200)
        Setlayout = QtWidgets.QHBoxLayout(Setbox)
        Setlayout.addWidget(cancelBtn)
        Setlayout.addWidget(setBtn)

        box0 = QtWidgets.QWidget(self)
        box0.setGeometry(50, 150, 150, 150)
        layout0 = QtWidgets.QVBoxLayout(box0)
        layout0.addWidget(self.button0)

        box1 = QtWidgets.QWidget(self)
        box1.setGeometry(50, 310, 150, 150)
        layout1 = QtWidgets.QVBoxLayout(box1)
        layout1.addWidget(self.button1)

        box2 = QtWidgets.QWidget(self)
        box2.setGeometry(50, 470, 150, 150)
        layout2 = QtWidgets.QVBoxLayout(box2)
        layout2.addWidget(self.button2)

        box3 = QtWidgets.QWidget(self)
        box3.setGeometry(50, 630, 150, 150)
        layout3 = QtWidgets.QVBoxLayout(box3)
        layout3.addWidget(self.button3)

        box4 = QtWidgets.QWidget(self)
        box4.setGeometry(210, 150, 150, 150)
        layout4 = QtWidgets.QVBoxLayout(box4)
        layout4.addWidget(self.button4)

        box5 = QtWidgets.QWidget(self)
        box5.setGeometry(210, 310, 150, 150)
        layout5 = QtWidgets.QVBoxLayout(box5)
        layout5.addWidget(self.button5)

        box6 = QtWidgets.QWidget(self)
        box6.setGeometry(210, 470, 150, 150)
        layout6 = QtWidgets.QVBoxLayout(box6)
        layout6.addWidget(self.button6)

        box7 = QtWidgets.QWidget(self)
        box7.setGeometry(210, 630, 150, 150)
        layout7 = QtWidgets.QVBoxLayout(box7)
        layout7.addWidget(self.button7)

    # def tempData(self, portStyle, portNumber, startX, startY, portWidth, portHeight):
    def tempData(self, fpgaEditID):
        # old data in FPGA
        deviceID = self.data["fpgaID"][fpgaEditID]["deviceID"]
        currentPortStyle = self.data["fpgaID"][fpgaEditID]["portStyle"]
        portNumber = self.data["fpgaID"][fpgaEditID]["portNumber"]
        startX = self.data["fpgaID"][fpgaEditID]["startX"]  # number 0 port
        startY = self.data["fpgaID"][fpgaEditID]["startY"]  # number 0 port
        portWidth = self.data["fpgaID"][fpgaEditID]["portWidth"]
        portHeight = self.data["fpgaID"][fpgaEditID]["portHeight"]
        wayNum = self.data["fpgaID"][fpgaEditID]["portWay"]
        portStyleNum = self.data["fpgaID"][fpgaEditID]["portStyle"]
        reverse = False

        print("deviceID = ", deviceID)
        print("fpgaEditID = ", fpgaEditID)

        if wayNum != self.Bbox.currentIndex():
            wayNum = self.Bbox.currentIndex()
            self.data["fpgaID"][fpgaEditID]["portWay"] = self.Bbox.currentIndex()
            self.writeData = True

        if self.WHInput2.text() != "":
            portHeight = self.WHInput2.text()
            self.data["fpgaID"][fpgaEditID]["portHeight"] = self.WHInput2.text()
            self.WHInput2.setPlaceholderText(self.WHInput2.text())
            self.writeData = True
        if self.WHInput1.text() != "":
            portWidth = self.WHInput1.text()
            self.data["fpgaID"][fpgaEditID]["portWidth"] = self.WHInput1.text()
            self.WHInput1.setPlaceholderText(self.WHInput1.text())
            self.writeData = True
        if self.XYInput1.text() != "":
            startX = self.XYInput1.text()
            self.data["fpgaID"][fpgaEditID]["startX"] = self.XYInput1.text()
            self.XYInput1.setPlaceholderText(self.XYInput1.text())
            self.writeData = True
        if self.XYInput2.text() != "":
            startY = self.XYInput2.text()
            self.data["fpgaID"][fpgaEditID]["startY"] = self.XYInput2.text()
            self.XYInput2.setPlaceholderText(self.XYInput2.text())
            self.writeData = True
        if self.portInput.text() != "":
            portNumber = self.portInput.text()
            self.data["fpgaID"][fpgaEditID]["portNumber"] = self.portInput.text()
            self.data["fpgaID"][fpgaEditID]["portWay"] = self.Bbox.currentIndex()
            self.portInput.setPlaceholderText(self.portInput.text())
            self.writeData = True

        if self.reverseInput.text() != "0" and self.reverseInput.text() != "":
            self.reverseInput = self.reverseInput.text()
            reverse = True
            # print('reverseInput = ' + reverseInput)
            # return

        ''' FPGA read/write '''
        writePortStyle = FPGACmdCenter(ETH_DEV, protocolDict["sourceAddress"])
        writePortStyle.write_fpga_register(deviceID, "panelWay", portStyleNum)

        for n in range(int(portNumber) + 1):
            writePortStyle.write_fpga_register(deviceID, 'portWidth_p{}'.format(str(n)), portWidth)
            writePortStyle.write_fpga_register(deviceID, 'portHeight_p{}'.format(str(n)), portHeight)

        # self.group.checkedId()
        if reverse:
            tempX = []
            tempY = []

        match int(currentPortStyle):
            case 0 | 1 | 2 | 3:
                if wayNum == 0:  # ⬆
                    for n in range(int(portNumber) + 1):
                        start_Y = int(startY) - n * int(portHeight)
                        start_X = int(startX)
                        if start_Y < 0:
                            break
                        if reverse:
                            tempX.append(start_X)
                            tempY.append(start_Y)
                        else:
                            writePortStyle.write_fpga_register(deviceID, 'startX_p{}'.format(str(n)), str(start_X))
                            writePortStyle.write_fpga_register(deviceID, 'startY_p{}'.format(str(n)), str(start_Y))
                            print('start = (' + str(start_X) + ', ' + str(start_Y) + ')')
                if wayNum == 1:  # ⬇
                    for n in range(int(portNumber) + 1):
                        start_Y = int(startY) + n * int(portHeight)
                        start_X = int(startX)
                        if start_Y < 0:
                            break
                        if reverse:
                            tempX.append(start_X)
                            tempY.append(start_Y)
                        else:
                            writePortStyle.write_fpga_register(deviceID, 'startX_p{}'.format(str(n)), str(start_X))
                            writePortStyle.write_fpga_register(deviceID, 'startY_p{}'.format(str(n)), str(start_Y))
                            print('start = (' + str(start_X) + ', ' + str(start_Y) + ')')

            case 4 | 5 | 6 | 7:
                if wayNum == 2:  # ⬅
                    for n in range(int(portNumber) + 1):
                        start_X = int(startX) - n * int(portWidth)
                        start_Y = int(startY)
                        if start_X < 0:
                            break
                        if reverse:
                            tempX.append(start_X)
                            tempY.append(start_Y)
                        else:
                            writePortStyle.write_fpga_register(deviceID, 'startX_p{}'.format(str(n)), str(start_X))
                            writePortStyle.write_fpga_register(deviceID, 'startY_p{}'.format(str(n)), str(start_Y))
                            print('start = (' + str(start_X) + ', ' + str(start_Y) + ')')
                if wayNum == 3:  # ⮕
                    for n in range(int(portNumber) + 1):
                        start_X = int(startX) + n * int(portWidth)
                        start_Y = int(startY)
                        if start_X < 0:
                            break
                        if reverse:
                            tempX.append(start_X)
                            tempY.append(start_Y)
                        else:
                            writePortStyle.write_fpga_register(deviceID, 'startX_p{}'.format(str(n)), str(start_X))
                            writePortStyle.write_fpga_register(deviceID, 'startY_p{}'.format(str(n)), str(start_Y))
                            print('start = (' + str(start_X) + ', ' + str(start_Y) + ')')
                # print('currentPortStyle = ', currentPortStyle)
            # case _:

        if reverse:
            outputX = []
            outputY = []
            portCount = 0
            print("reverse")
            for i in range(0, len(tempX)-1, int(self.reverseInput)):
                outputX = tempX[i:i + int(self.reverseInput)]
                outputX.reverse()
                outputY = tempY[i:i + int(self.reverseInput)]
                outputY.reverse()
                for j in range(0, int(self.reverseInput)):
                    print('start = (' + str(outputX[j]) + ', ' + str(outputY[j]) + ')')
                    print("start _p = ", portCount)
                    # print("startY_p = ", outputY[j])
                    # no verify
                    writePortStyle.write_fpga_register(deviceID, 'startX_p{}'.format(str(portCount)), str(outputX[j]))
                    writePortStyle.write_fpga_register(deviceID, 'startY_p{}'.format(str(portCount)), str(outputY[j]))
                    portCount = portCount + 1
            # print("reverse outputX = ", outputX)
            # print("reverse outputY = ", outputY)
            # print(tempY)
            # print('reverse startY = ' + tempX)
            # print('reverse startY = ' + tempY)
            # int(portNumber) % int(self.reverseInput) != 0

        if self.writeData:
            with open("led_config/dataFPGA.json", "w") as jsonFile:
                json.dump(self.data, jsonFile, indent=2)
                print('write json')

        self.close()
        # app.quit()
        # os.execl(sys.executable, sys.executable, *sys.argv)

    # change img
    def portStyle(self, text, fpgaEditID):
        self.writeData = True
        # self.portStyleNum = text
        img = QtGui.QImage('materials/' + text + '.png')
        self.portStyleImg.setPixmap(QtGui.QPixmap(img).scaled(150, 150))
        self.data["fpgaID"][fpgaEditID]["portStyle"] = text

    def cancel(self):
        self.close()