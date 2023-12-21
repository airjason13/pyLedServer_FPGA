from PyQt5.QtWidgets import QTreeWidget, QApplication, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent


class CTreeWidget(QTreeWidget):
    qsignal_mouse_move = (pyqtSignal(QMouseEvent))

    def mouseMoveEvent(self, event):
        self.qsignal_mouse_move.emit(event)
