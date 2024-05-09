from PyQt5 import QtWidgets, QtGui, QtCore, QtNetwork
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
import json
import atexit
import os
from jqlocalserver import get_server_name
from global_def import *
_tries = 0


def send_message(**data):
    socket = QtNetwork.QLocalSocket()
    # log("in send message, SERVER:", get_server_name())
    # socket.connectToServer(get_server_name(), QtCore.QIODevice.WriteOnly)
    socket.connectToServer(get_server_name(), QtCore.QIODevice.ReadWrite)
    if socket.waitForConnected(500):
        socket.write(json.dumps(data).encode('utf-8'))
        if not socket.waitForBytesWritten(2000):
            raise RuntimeError('could not write to socket: %s' %
                  socket.errorString())
        socket.waitForReadyRead(3000)
        try:
            b_recv_data = socket.readAll()
            recv_data = b_recv_data.data().decode()
            # log.debug("recv_data = %s", recv_data)
        except Exception as e:
            log.fatal(e)
        socket.disconnectFromServer()
        socket.close()
        socket.deleteLater()
    elif socket.error() == QtNetwork.QAbstractSocket.HostNotFoundError:
        global _tries
        if _tries < 10:
            if not _tries:
                if QtCore.QProcess.startDetached('python', [os.path.abspath(__file__)]):
                    atexit.register(lambda: send_message(shutdown=True))
                else:
                    raise RuntimeError('could not start dialog server')
            _tries += 1
            QtCore.QThread.msleep(100)
            send_message(**data)
        else:
            raise RuntimeError('could not connect to server: %s' % socket.errorString())

    else:
        raise RuntimeError('could not send data: %s' % socket.errorString())



