from c_mainwindow import MainUi
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets
import sys
import qtmodern.styles
import qtmodern.windows
from global_def import *


if __name__ == '__main__':
    sys.setrecursionlimit(100000)

    #cpu_available = os.sched_getaffinity(os.getpid())
    #os.sched_setaffinity(os.getpid(), list(cpu_available)[:1])
    ''' qt app instruction '''
    qt_app = QApplication(sys.argv)
    main_window = MainUi()
    main_window.show()
    # gui = qtmodern.windows.ModernWindow(main_window)
    # gui.sizePolicy(QtWidgets.QSizePolicy.Expanding)
    # gui.setSizePolicy(qtmodern.windows.QSizePolicy.)
    # gui.show()

    sys.exit(qt_app.exec_())
