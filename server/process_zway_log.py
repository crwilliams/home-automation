from Queue import Queue

import serial

from Data.ZWaveAPI import ZWaveAPI

from Threads.EphemerisThread import EphemerisThread
from Threads.ExternalQueueReaderThread import ExternalQueueReaderThread
from Threads.InboundThread import InboundThread
from Threads.OutboundThread import OutboundThread
from Threads.InputReaderThread import FileInputReaderThread
from Threads.ServerThread import ServerThread
from Threads.TimerThread import TimerThread
from constants import Constants
from Data.State import State


try:
    SERIAL = serial.Serial(Constants.serial_device, 9600)
except OSError:
    print 'Unable to open %s' % Constants.serial_device


def main():
    input_queue = Queue()
    output_queue = Queue()

    State().zwave_api = ZWaveAPI()
    ServerThread().start()
    FileInputReaderThread(
        input_queue, output_queue, Constants.input_log_filename).start()
    ExternalQueueReaderThread(input_queue).start()
    OutboundThread(output_queue).start()
    EphemerisThread(input_queue, Constants.city).start()
    TimerThread(input_queue).start()
    InboundThread(input_queue).run()  # This thread is being run as the parent.


if __name__ == '__main__':
    main()
