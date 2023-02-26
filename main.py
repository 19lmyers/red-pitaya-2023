#!/usr/bin/python

import sys
import matplotlib
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import QApplication, QMainWindow

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from gui import Ui_MainWindow
from daemon import Daemon
from event import *

matplotlib.use('QtAgg')
# plt.style.use("dark_background")


daemonThread = None
dameonConnected = False


def connect_daemon(ip: str):
    global app, daemonThread, dameonConnected

    daemonThread = Daemon(app, ip)
    daemonThread.start()

    dameonConnected = True


def send_daemon(msg: str):
    global daemonThread

    if daemonThread:
        daemonThread.send(msg)


def disconnect_daemon():
    global daemonThread, dameonConnected

    if daemonThread:
        daemonThread.stop()

    daemonThread = None

    dameonConnected = False


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=2, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.connect_signals_slots()

    def connect_signals_slots(self):
        self.connectButton.clicked.connect(self.on_connect)
        self.sendButton.clicked.connect(self.on_send)

    def on_connect(self):
        global dameonConnected

        if dameonConnected:
            disconnect_daemon()

            self.connectButton.setText("Connect")
            self.ipText.setReadOnly(False)

            self.sendButton.setEnabled(False)
            self.messageText.setEnabled(False)
        else:
            self.connectButton.setText("Disconnect")
            self.ipText.setReadOnly(True)

            ip = self.ipText.text()

            self.textLog.insertPlainText("Connecting to " + ip + "\n")

            connect_daemon(ip)

    def on_send(self):
        global daemonThread

        text = self.messageText.text()
        if not text:
            return

        window.textLog.insertPlainText(text + '\n')
        self.messageText.setText("")

        send_daemon(text)


morse = {
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    '/': '-..-.', '@': '.--.-.', '\'': '.----.', '!': '-.-.--', '(': '-.--.',
    ')': '-.--.-', '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.','$': '...-..'
}

graph = None


def decrypt_morse(text: str):
    patterns = dict((value, key) for key, value in morse.items())
    return ''.join(' ' if c == '/' else patterns.get(c) or '?' for c in text.split(' '))


class Application(QApplication):
    def event(self, event: QEvent):
        global window
        global graph

        if event.type() == EVENT_DAEMON_CONNECTED:
            window.sendButton.setEnabled(True)
            window.messageText.setEnabled(True)

            window.textLog.insertPlainText("Connected!\n")

        elif event.type() == EVENT_DAEMON_DISCONNECTED:
            window.textLog.insertPlainText("Disconnected.\n")

        elif event.type() == EVENT_DAEMON_MSG_RECEIVED:
            message = decrypt_morse(event.msg)

            window.textLog.insertPlainText("[" + event.msg + "]: " + message + "\n")

        elif event.type() == EVENT_DAEMON_PAYLOAD_RECEIVED:
            payload = event.payload

            if graph:
                window.graph.removeWidget(graph)

            graph = MplCanvas(self)
            graph.axes.plot(payload)

            window.graph.addWidget(graph)

        elif event.type() == EVENT_DAEMON_FATAL_ERROR:
            window.textLog.insertPlainText("A fatal error occured: {!s:s}\n".format(event.ex))

            window.connectButton.setText("Connect")
            window.ipText.setReadOnly(False)

            window.sendButton.setEnabled(False)
            window.messageText.setEnabled(False)

            disconnect_daemon()

        return QApplication.event(self, event)


sys.argv += ['-platform', 'windows:darkmode=2']
app = Application(sys.argv)
app.setStyle('Fusion')

window = Window()
window.show()

app.exec()

if daemonThread:
    daemonThread.stop()

sys.exit()
