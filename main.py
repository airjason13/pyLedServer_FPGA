from flask import Flask
from c_mainwindow import MainUi
from PyQt5.QtWidgets import QApplication
from global_def import *

# start of the flask import and declare, do not change the seq
from flaskplugin import FlaskPlugin

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
from flask_routes.routes import *
# end of the flask import and declare, do not change the seq

if __name__ == '__main__':
    sys.setrecursionlimit(100000)

    # cpu_available = os.sched_getaffinity(os.getpid())
    # os.sched_setaffinity(os.getpid(), list(cpu_available)[:1])

    ''' qt app instruction '''
    qt_app = QApplication(sys.argv)
    main_window = MainUi()
    main_window.show()

    flask_app = FlaskPlugin(app_=app)
    flask_app.start()

    # gui = qtmodern.windows.ModernWindow(main_window)
    # gui.sizePolicy(QtWidgets.QSizePolicy.Expanding)
    # gui.setSizePolicy(qtmodern.windows.QSizePolicy.)
    # gui.show()

    sys.exit(qt_app.exec_())
