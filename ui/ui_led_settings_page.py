from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QFileSystemWatcher
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton
from global_def import *
from media_engine.media_engine import MediaEngine
# from ext_qt_widgets.system_file_watcher import FileWatcher

import threading
import binascii
import socket
import struct
import json
import os

# read FPGA data
with open("led_config/dataFPGA.json", "r") as jsonFile:
    data = json.load(jsonFile)

class LedSettingsPage(QWidget):
    # FileWatcher(QWidget)
    signal_file_changed = pyqtSignal(str)

    def __init__(self, _main_window, _frame: QWidget, _name: str,  media_engine: MediaEngine, fpga_list: [], **kwargs):
        super(LedSettingsPage, self).__init__(**kwargs)
        self.main_windows = _main_window
        self.frame = _frame
        self.widget = QWidget(self.frame)
        self.name = _name
        self.nw = None
        #self.setStyleSheet("background-color: #222222;")
        
        '''
        self.watcher = FileWatcher(self)
        self.watcher.fileChanged.connect(self.file_changed)
        '''
        # watch if json file change
        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(os.getcwd() + '/led_config/dataFPGA.json')
        self.watcher.fileChanged.connect(self.file_changed)
        # print("os.getcwd() = ", os.getcwd())
        
        self.init_ui()

    def init_ui(self):
        ledWidthLabel = QtWidgets.QLabel('LED Width : ')
        self.ledWidthInput = QtWidgets.QLineEdit(self)
        self.ledWidthInput.setAlignment(QtCore.Qt.AlignCenter)
        self.ledWidthInput.setPlaceholderText(data["ledWidth"])
        ledHeightLabel = QtWidgets.QLabel('   LED Height : ')
        self.ledHeightInput = QtWidgets.QLineEdit(self)
        self.ledHeightInput.setAlignment(QtCore.Qt.AlignCenter)
        self.ledHeightInput.setPlaceholderText(data["ledHeight"])
        setBtn = QtWidgets.QPushButton('  Set  ')  # 建立按鈕

        box = QtWidgets.QWidget(self)       # 建立放置 QFormLayout 的 Widget
        box.setGeometry(50,0,1100,150)
        
        layout = QtWidgets.QHBoxLayout(box)
        layout.addWidget(ledWidthLabel)
        layout.addWidget(self.ledWidthInput)
        layout.addWidget(ledHeightLabel)
        layout.addWidget(self.ledHeightInput)
        layout.addWidget(setBtn)
        
        boxG = QtWidgets.QWidget(self)        # 建立放 QGridLayout 的元件
        boxG.setGeometry(50,200,1100,700)       # 指定大小位置
        
        groupBox = QtWidgets.QGroupBox('FPGA Port Style')
        grid = QtWidgets.QGridLayout()    # 建立 QGridLayout

        self.portStyleList = []
        self.portImgList = []
        
        for n in range(len(data["fpgaID"])):
            portStyleLabel = QtWidgets.QLabel('FPGA ID = ' + data["fpgaID"][n]["id"] + '\t')
            portStyleSet = QtWidgets.QLabel(
                                    'Start( x , y ) = ( ' + data["fpgaID"][n]["startX"] + ' , ' + data["fpgaID"][n]["startY"] + ' )' +
                                    '\nW x H = ' + data["fpgaID"][n]["portWidth"] + ' x ' + data["fpgaID"][n]["portHeight"]
                                )
            self.portStyleList.append(portStyleSet)
            
            portImg = QtWidgets.QLabel(self)
            img = QtGui.QImage('materials/' + data["fpgaID"][n]["portStyle"] + '.png')                      # 讀取圖片
            portImg.setPixmap(QtGui.QPixmap(img).scaled(150, 150)) # 加入圖片
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
        
        setBtn.clicked.connect(self.setWidthHeight)
        #self.portStyleBtn.clicked.connect(lambda:self.fpgaEdit(data["fpgaID"][1]["id"]))
        
        
    def setWidthHeight(self):
        #self.refresh()
        writeData = False
        if self.ledWidthInput.text()!= "":
            self.ledWidthInput.setPlaceholderText(self.ledWidthInput.text())
            data["ledWidth"] = self.ledWidthInput.text()
            writeData = True
        if self.ledHeightInput.text()!= "":
            self.ledHeightInput.setPlaceholderText(self.ledHeightInput.text())
            data["ledHeight"] = self.ledHeightInput.text()
            writeData = True
        if writeData:
            with open("led_config/dataFPGA.json", "w") as jsonFile:
                json.dump(data, jsonFile, indent=2)
                log.debug('write json')
        
    def fpgaEdit(self):
        sender = self.sender()
        pushButton = self.findChild(QtWidgets.QPushButton, sender.objectName())
        fpgaEditID = pushButton.objectName()
        # print('fpgaEdit = ', fpgaEditID)
        
        if self.nw is None or self.nw.close():
            self.nw = portSettingWindow(fpgaEditID)   # 連接新視窗
            self.nw.show()                  # 顯示新視窗
            x = self.nw.pos().x()           # 取得新視窗目前 x 座標
            y = self.nw.pos().y()           # 取得新視窗目前 y 座標
            self.nw.move(x+100, y+100)      # 移動新視窗位置
        else:
            self.nw.close()
            self.nw = None
        
        
    def file_changed(self, path):
        self.signal_file_changed.emit(path)
        # print('file_changed')
        # print('self.portStyleList = ', self.portStyleList)
        
        for n in range(len(data["fpgaID"])):
            self.portStyleList[n].setText(
                                    'Start( x , y ) = ( ' + data["fpgaID"][n]["startX"] + ' , ' + data["fpgaID"][n]["startY"] + ' )' +
                                    '\nW x H = ' + data["fpgaID"][n]["portWidth"] + ' x ' + data["fpgaID"][n]["portHeight"]
                                )
            #self.portStyleSet.setObjectName('portStyle'+str(n))
            img = QtGui.QImage('materials/' + data["fpgaID"][n]["portStyle"] + '.png')
            self.portImgList[n].setPixmap(QtGui.QPixmap(img).scaled(150, 150)) # 加入圖片

    def func_test_btn(self):
        log.debug("func test btn clicked")
        

class portSettingWindow(QtWidgets.QWidget):
    def __init__(self, fpgaEditID):
        super().__init__()
        self.setWindowTitle('Port Setting')
        self.setStyleSheet("background-color: #222222;")
        self.resize(1500,900)
        self.writeData = False
        #print('FPGA fpgaEditID = ' , fpgaEditID)
        #self.fpgaEditID = fpgaEditID
        self.ui(fpgaEditID)

    def ui(self, fpgaEditID):
        fpgaEditID = int(fpgaEditID)
        fpgaIDLabel = QtWidgets.QLabel('FPGA ID = ' + data["fpgaID"][fpgaEditID]["id"])
        # print('FPGA fpgaEditID = ' , fpgaEditID)
        currentLabel = QtWidgets.QLabel('Current Port Style  ⇨  ')
        self.portStyleImg = QtWidgets.QLabel(self)
        img = QtGui.QImage('materials/' + data["fpgaID"][fpgaEditID]["portStyle"] + '.png')                # 讀取圖片
        self.portStyleImg.setPixmap(QtGui.QPixmap(img).scaled(150, 150))    # 加入圖片
        
        setPortLabel = QtWidgets.QLabel('From 0 port to ')
        self.portInput = QtWidgets.QLineEdit(self)
        self.portInput.setMaxLength(2)
        self.portInput.setPlaceholderText(data["fpgaID"][fpgaEditID]["portNumber"])
        self.portInput.setAlignment(QtCore.Qt.AlignCenter)
        setLabel = QtWidgets.QLabel(' port\t')
        
        XYLabel1 = QtWidgets.QLabel('Start ( X , Y ) = ( ')
        self.XYInput1 = QtWidgets.QLineEdit(self)
        self.XYInput1.setAlignment(QtCore.Qt.AlignCenter)
        self.XYInput1.setPlaceholderText(data["fpgaID"][fpgaEditID]["startX"])
        XYLabel3 = QtWidgets.QLabel(' , ')
        self.XYInput2 = QtWidgets.QLineEdit(self)
        self.XYInput2.setAlignment(QtCore.Qt.AlignCenter)
        self.XYInput2.setPlaceholderText(data["fpgaID"][fpgaEditID]["startY"])
        XYLabel2 = QtWidgets.QLabel(' )\t')
        
        WHLabel1 = QtWidgets.QLabel('Width , Height = ( ')
        self.WHInput1 = QtWidgets.QLineEdit(self)
        self.WHInput1.setAlignment(QtCore.Qt.AlignCenter)
        self.WHInput1.setPlaceholderText(data["fpgaID"][fpgaEditID]["portWidth"])
        WHLabel2 = QtWidgets.QLabel(' , ')
        self.WHInput2 = QtWidgets.QLineEdit(self)
        self.WHInput2.setAlignment(QtCore.Qt.AlignCenter)
        self.WHInput2.setPlaceholderText(data["fpgaID"][fpgaEditID]["portHeight"])
        WHLabel3 = QtWidgets.QLabel(' )\t')
        
        cancelBtn = QtWidgets.QPushButton('  Cancel  ') # 建立按鈕
        setBtn = QtWidgets.QPushButton('  Set  ')       # 建立按鈕
        cancelBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        setBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        
        setBtn.clicked.connect(lambda:self.tempData(fpgaEditID))
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
        
        self.button0.clicked.connect(lambda:self.portStyle('0', fpgaEditID))
        self.button1.clicked.connect(lambda:self.portStyle('1', fpgaEditID))
        self.button2.clicked.connect(lambda:self.portStyle('2', fpgaEditID))
        self.button3.clicked.connect(lambda:self.portStyle('3', fpgaEditID))
        self.button4.clicked.connect(lambda:self.portStyle('4', fpgaEditID))
        self.button5.clicked.connect(lambda:self.portStyle('5', fpgaEditID))
        self.button6.clicked.connect(lambda:self.portStyle('6', fpgaEditID))
        self.button7.clicked.connect(lambda:self.portStyle('7', fpgaEditID))
        
        Lbox = QtWidgets.QWidget(self)       # 建立放置 QFormLayout 的 Widget
        Lbox.setGeometry(50,0,250,100)
        Llayout = QtWidgets.QVBoxLayout(Lbox)
        Llayout.addWidget(fpgaIDLabel)
        
        Cbox = QtWidgets.QWidget(self)
        Cbox.setGeometry(450,0,800,200)
        Clayout = QtWidgets.QHBoxLayout(Cbox)
        Clayout.addWidget(currentLabel)
        Clayout.addWidget(self.portStyleImg)
        
        Sbox = QtWidgets.QWidget(self)    
        Sbox.setGeometry(450,200,800,150)
        Slayout = QtWidgets.QHBoxLayout(Sbox)
        Slayout.addWidget(setPortLabel)
        Slayout.addWidget(self.portInput)
        Slayout.addWidget(setLabel)
        
        XYbox = QtWidgets.QWidget(self)    
        XYbox.setGeometry(450,350,850,150)
        Slayout = QtWidgets.QHBoxLayout(XYbox)
        Slayout.addWidget(XYLabel1)
        Slayout.addWidget(self.XYInput1)
        Slayout.addWidget(XYLabel3)
        Slayout.addWidget(self.XYInput2)
        Slayout.addWidget(XYLabel2)
        # Slayout.addWidget(XYBtn)
        
        WHbox = QtWidgets.QWidget(self)    
        WHbox.setGeometry(450,500,900,150)
        Slayout = QtWidgets.QHBoxLayout(WHbox)
        Slayout.addWidget(WHLabel1)
        Slayout.addWidget(self.WHInput1)
        Slayout.addWidget(WHLabel2)
        Slayout.addWidget(self.WHInput2)
        Slayout.addWidget(WHLabel3)
        
        Setbox = QtWidgets.QWidget(self)    
        Setbox.setGeometry(1100,650,300,200)
        Setlayout = QtWidgets.QHBoxLayout(Setbox)
        Setlayout.addWidget(cancelBtn)
        Setlayout.addWidget(setBtn)
        
        box0 = QtWidgets.QWidget(self)
        box0.setGeometry(50,150,150,150)
        layout0 = QtWidgets.QVBoxLayout(box0)
        layout0.addWidget(self.button0)
        
        box1 = QtWidgets.QWidget(self)
        box1.setGeometry(50,310,150,150)
        layout1 = QtWidgets.QVBoxLayout(box1)
        layout1.addWidget(self.button1)
        
        box2 = QtWidgets.QWidget(self)
        box2.setGeometry(50,470,150,150)
        layout2 = QtWidgets.QVBoxLayout(box2)
        layout2.addWidget(self.button2)
        
        box3 = QtWidgets.QWidget(self)
        box3.setGeometry(50,630,150,150)
        layout3 = QtWidgets.QVBoxLayout(box3)
        layout3.addWidget(self.button3)
        
        box4 = QtWidgets.QWidget(self)
        box4.setGeometry(210,150,150,150)
        layout4 = QtWidgets.QVBoxLayout(box4)
        layout4.addWidget(self.button4)
        
        box5 = QtWidgets.QWidget(self)
        box5.setGeometry(210,310,150,150)
        layout5 = QtWidgets.QVBoxLayout(box5)
        layout5.addWidget(self.button5)
        
        box6 = QtWidgets.QWidget(self)
        box6.setGeometry(210,470,150,150)
        layout6 = QtWidgets.QVBoxLayout(box6)
        layout6.addWidget(self.button6)
        
        box7 = QtWidgets.QWidget(self)
        box7.setGeometry(210,630,150,150)
        layout7 = QtWidgets.QVBoxLayout(box7)
        layout7.addWidget(self.button7)
        
        
    # def tempData(self, portStyle, portNumber, startX, startY, portWidth, portHeight):
    def tempData(self, fpgaEditID):
        if self.WHInput2.text() != "":
            data["fpgaID"][fpgaEditID]["portHeight"] = self.WHInput2.text()
            self.WHInput2.setPlaceholderText(self.WHInput2.text())
            self.writeData = True
        if self.WHInput1.text() != "":
            data["fpgaID"][fpgaEditID]["portWidth"] = self.WHInput1.text()
            self.WHInput1.setPlaceholderText(self.WHInput1.text())
            self.writeData = True
        if self.XYInput1.text() != "":
            data["fpgaID"][fpgaEditID]["startX"] = self.XYInput1.text()
            self.XYInput1.setPlaceholderText(self.XYInput1.text())
            self.writeData = True
        if self.XYInput2.text() != "":
            data["fpgaID"][fpgaEditID]["startY"] = self.XYInput2.text()
            self.XYInput2.setPlaceholderText(self.XYInput2.text())
            self.writeData = True
        if self.portInput.text() != "":
            data["fpgaID"][fpgaEditID]["portNumber"] = self.portInput.text()
            self.portInput.setPlaceholderText(self.portInput.text())
            self.writeData = True
            
        if self.writeData:
            with open("led_config/dataFPGA.json", "w") as jsonFile:
                json.dump(data, jsonFile, indent=2)
                log.debug('write json')
        
        self.close()
        #app.quit()
        #os.execl(sys.executable, sys.executable, *sys.argv)
        
    # change img
    def portStyle(self, text, fpgaEditID):
        self.writeData = True
        img = QtGui.QImage('materials/' + text + '.png')
        self.portStyleImg.setPixmap(QtGui.QPixmap(img).scaled(150, 150))
        data["fpgaID"][fpgaEditID]["portStyle"] = text
        
    def cancel(self):
        self.close()