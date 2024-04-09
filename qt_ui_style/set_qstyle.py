import qdarkstyle

from global_def import *


def set_qstyle_dark(QObject):
    try:
        QObject.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() + \
                              """
                              QMenu{
                                  button-layout : 2;
                                  font: bold 16pt "Brutal Type";
                                  border: 3px solid #FFA042;
                                  border-radius: 8px;
                                  }
                              """)
    except Exception as e:
        log.error(e)

