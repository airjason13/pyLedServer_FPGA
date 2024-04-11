

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
QPushPlayButton_Style = """
        QPushButton {
            background-color: #4CAF50;  /* Green background */
            color: white;
            border: 2px solid #4CAF50;  /* Green border */
            padding: 10px 15px;
            border-radius: 4px;  /* Rounded corners */
        }

        QPushButton:pressed {
            background-color: #388E3C;  /* Darker green for pressed state */
            border: 2px solid #388E3C;  /* Darker green border for pressed state */
            padding: 12px 13px;  /* Slightly larger padding to simulate a press effect */
            margin-top: 2px;  /* Move the button down to simulate being pressed */
            margin-left: 2px;
        }
    """
QPushStopButton_Style = """
        QPushButton {
            background-color: #f44336;  /* Red background */
            color: white;
            border: 2px solid #f44336;  /* Red border */
            padding: 10px 15px;
            border-radius: 4px;  /* Rounded corners */
        }

        QPushButton:pressed {
            background-color: #D32F2F;  /* Darker red for pressed state */
            border: 2px solid #D32F2F;  /* Darker red border for pressed state */
            padding: 12px 13px;  /* Slightly larger padding to simulate a press effect */
            margin-top: 2px;  /* Move the button down to simulate being pressed */
            margin-left: 2px;
        }
    """