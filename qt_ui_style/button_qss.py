

# PushButton font and size
QFont_Style_Default = 'Times'
QFont_Style_Size_XL = 32
QFont_Style_Size_L = 24
QFont_Style_Size_M = 16
QFont_Style_Size_S = 12

QPushButton_Page_Selector_Min_Width = 240
QPushButton_Page_Selector_Min_Height = 64

QPushButton_Style = """
            QPushButton {
                border: 2px solid #223322;
                border-radius: 6px;
                background-color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #444444, stop: 1 #aaaaaa);
                color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #000000, stop: 1 #444444);
                min-width: 80px;
                max-width: 240px;
                width: 240px;
                height:64px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #000000, stop: 1 #00aaff);
            }
            QPushButton:pressed {
                background-color: #FFA823;
                color: #000000;
                font: bold 14px;
            }
        """
