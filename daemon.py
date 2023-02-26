import struct
import threading
import time

import redpitaya_scpi as scpi

from queue import Queue

from PyQt6.QtWidgets import QApplication

from event import *


class Daemon(threading.Thread):
    def __init__(self, app: QApplication, ip: str):
        threading.Thread.__init__(self)
        self.app = app
        self.ip = ip
        self.run_flag = False
        self.send_queue = Queue()

    def run(self):
        try:
            rp_s = scpi.scpi(str(self.ip))
        except Exception as ex:
            QApplication.postEvent(self.app, EventDaemonFatalError(ex))
            return

        QApplication.postEvent(self.app, QEvent(EVENT_DAEMON_CONNECTED))

        self.run_flag = True

        configure(rp_s)

        while self.run_flag:
            try:
                main(rp_s, self.send_queue, self.app)
            except Exception as ex:
                self.run_flag = False
                QApplication.postEvent(self.app, EventDaemonFatalError(ex))
                raise ex  # TODO remove

        rp_s.close()

        QApplication.postEvent(self.app, QEvent(EVENT_DAEMON_DISCONNECTED))

    def send(self, msg: str):
        self.send_queue.put(msg)

    def stop(self):
        self.run_flag = False


def configure(rp_s: scpi):
    rp_s.tx_txt("ACQ:RST")
    rp_s.tx_txt("ACQ:DATA:UNITS VOLTS")
    rp_s.tx_txt("ACQ:DATA:FORMAT BIN")
    rp_s.tx_txt("ACQ:SOUR1:GAIN HV")
    rp_s.tx_txt("ACQ:DEC 64")


trigger_waiting = False


def main(rp_s: scpi, send_queue: Queue, app: QApplication):
    global trigger_waiting

    if not trigger_waiting:
        rp_s.tx_txt("ACQ:START")
        rp_s.tx_txt("ACQ:TRIG CH1_NE")
        rp_s.tx_txt("ACQ:TRIG:LEV 2.5 V")
        rp_s.tx_txt("ACQ:TRIG:DLY:NS 2500000")
        trigger_waiting = True

    rp_s.tx_txt('ACQ:TRIG:STAT?')
    time.sleep(1)
    if rp_s.rx_txt() == 'TD':
        trigger_waiting = False

        # rp_s.tx_txt("ACQ:TPOS?")
        # trigger_pos = int(rp_s.rx_txt())

        # rp_s.tx_txt("ACQ:WPOS?")
        # writer_pos = int(rp_s.rx_txt())

        # QApplication.postEvent(app, EventDaemonMsgReceived("{:n}, {:n}".format(trigger_pos, writer_pos)))

        # rp_s.tx_txt("ACQ:SOUR1:DATA:STA:END? {:n},{:n}".format(trigger_pos, writer_pos))
        rp_s.tx_txt("ACQ:SOUR1:DATA?")
        buff_byte = rp_s.rx_arb()
        if buff_byte:
            volts = [struct.unpack('!f', bytearray(buff_byte[i:i+4]))[0] for i in range(0, len(buff_byte), 4)]

            QApplication.postEvent(app, EventDaemonPayloadReceived(volts))

            was_high = True
            start_sample = 0
            end_sample = 0

            recv_msg = ''

            for index, volt in enumerate(volts):
                is_high = volt > 4.5

                if was_high is True and is_high is False:
                    # Falling edge, start counting
                    # QApplication.postEvent(app, EventDaemonMsgReceived("Falling"))
                    start_sample = index

                    num_samples = (start_sample - end_sample)

                    # QApplication.postEvent(app, EventDaemonMsgReceived("{:f} - {:f}: {:f}".format(end_sample, start_sample, num_samples)))

                    if 400 <= num_samples <= 800:
                        recv_msg += ' '
                    elif 1300 <= num_samples:
                        recv_msg += ' / '

                    was_high = False

                elif was_high is False and is_high is True:
                    # Rising edge, finish counting
                    # QApplication.postEvent(app, EventDaemonMsgReceived("Rising"))
                    end_sample = index

                    num_samples = (end_sample - start_sample)
                    # QApplication.postEvent(app, EventDaemonMsgReceived("{:f} - {:f}: {:f}".format(start_sample, end_sample, num_samples)))

                    if 200 <= num_samples <= 350:
                        recv_msg += '.'
                    elif 700 <= num_samples <= 800:
                        recv_msg += '-'

                    was_high = True

            QApplication.postEvent(app, EventDaemonMsgReceived(recv_msg))

    if not send_queue.empty():
        send_msg = send_queue.get()
        print("TODO SEND: " + send_msg)
        # TODO send message
