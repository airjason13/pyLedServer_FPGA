

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
                border: 2px solid #748CAB;
                border-radius: 16px;
                background-color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #1D2D44, stop: 1 #748CAB);
                color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #000000, stop: 1 #1D2D44);
                min-width: 80px;
                max-width: 240px;
                width: 240px;
                height:64px;
            }
            QPushButton:hover {
                color: #F0EBD8;
                background-color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #000000, stop: 1 #00aaff);
            }
            QPushButton:pressed {
                background-color: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                  stop: 0 #00aaff, stop: 1 #000000);
                color: #1D2D44;
                
            }
        """
