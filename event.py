from PyQt6.QtCore import QEvent


EVENT_DAEMON_CONNECTED = QEvent.registerEventType()

EVENT_DAEMON_MSG_RECEIVED = QEvent.registerEventType()

EVENT_DAEMON_PAYLOAD_RECEIVED = QEvent.registerEventType()

EVENT_DAEMON_FATAL_ERROR = QEvent.registerEventType()

EVENT_DAEMON_DISCONNECTED = QEvent.registerEventType()


class EventDaemonMsgReceived(QEvent):
    def __init__(self, msg):
        QEvent.__init__(self, EVENT_DAEMON_MSG_RECEIVED)
        self.msg = msg


class EventDaemonPayloadReceived(QEvent):
    def __init__(self, payload):
        QEvent.__init__(self, EVENT_DAEMON_PAYLOAD_RECEIVED)
        self.payload = payload


class EventDaemonFatalError(QEvent):
    def __init__(self, ex):
        QEvent.__init__(self, EVENT_DAEMON_FATAL_ERROR)
        self.ex = ex