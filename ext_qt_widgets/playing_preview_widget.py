import qdarkstyle
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QFrame


from global_def import log


class PlayingPreviewWindow(QWidget):

    def __init__(self):

        super(PlayingPreviewWindow, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                      """
                      QMenu{
                          button-layout : 2;
                          font: bold 16pt "Brutal Type";
                          border: 3px solid #FFA042;
                          border-radius: 8px;
                          }
                      """)
        self.setWindowTitle("Playing Preview")
        self.layout = None
        self.preview_label = None
        self.image_display_width = 400
        self.image_display_height = 300
        self.init_ui()

        # self.error_message_box.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def init_ui(self):
        self.setFixedSize(self.image_display_width, self.image_display_height)
        ''' Total frame layout'''
        self.layout = QGridLayout(self)
        layoutwidget = QFrame()
        layoutgridbox = QGridLayout()
        layoutwidget.setLayout(layoutgridbox)
        self.preview_label = QLabel()
        self.preview_label.setText("Playing Preview")
        layoutgridbox.addWidget(self.preview_label, 0, 1)
        self.layout.addWidget(layoutwidget)

    def refresh_image(self, np_image):
        log.debug("")
        qt_img = self.convert_ffmpeg_qt(np_image)
        self.preview_label.setPixmap(qt_img)

    def convert_ffmpeg_qt(self, ffmpeg_img):
        """Convert from an opencv image to QPixmap"""
        # rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = ffmpeg_img.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(ffmpeg_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.image_display_width, self.image_display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def set_visible(self, is_visible: bool):
        log.debug("")
        self.setVisible(is_visible)
