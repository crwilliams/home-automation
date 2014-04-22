from Queue import Queue
from collections import defaultdict
import urllib2

import serial

from Threads.EphemerisThread import EphemerisThread
from Threads.ExternalQueueReaderThread import ExternalQueueReaderThread
from Threads.InboundThread import InboundThread
from Threads.OutboundThread import OutboundThread
from Threads.InputReaderThread import FileInputReaderThread
from Threads.ServerThread import ServerThread
from Threads.TimerThread import TimerThread
from constants import Constants


class State(object):
    _instance = None
    rooms = None
    day_or_night = None
    init = None
    log = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(State, cls).__new__(cls)
            print 'creating singleton'
            cls._instance.rooms = defaultdict(Room)
            cls._instance.init = False
            cls._instance.log = []
        return cls._instance

    def get_dict(self):
        return {
            'rooms': dict(self.rooms),
            'day_or_night': self.day_or_night,
        }

    def log_init(self):
        self.init = True

    def is_init(self):
        return self.init

    def add_log_entry(self, timestamp, room, value):
        self.log.append({'time': timestamp, 'room': room, 'value': value})


class Room(object):
    _value = None
    _time = None

    def __repr__(self):
        return str(self._value)

    def update(self, timestamp, value):
        self._value = value
        self._time = timestamp

    def get_value(self):
        return self._value

    def get_time(self):
        return self._time


def set_lights(room, action):
    if room in Constants.config.keys():
        device = Constants.config[room]
    else:
        return False

    if device[2] == 'SwitchMultilevel' or device[2] == 'SwitchBinary':
        if action == 'on':
            action = 255
        elif action == 'off':
            action = 0

        action = int(action)

        if action == 255 or 0 <= action <= 100:
            url = (
                'http://127.0.0.1:8083/ZWaveAPI/Run/'
                'devices[%s].instances[%s].%s.Set(%s)' % (
                    device[0], device[1], device[2], action))
            urllib2.urlopen(url)
            return True
        else:
            return False
    elif device[2] == 'HomeEasy':
        command = '-'.join([str(x) for x in [
            device[0], device[1], action.upper()]])
        try:
            SERIAL.write(command)
        except NameError:
            print 'No serial device, cannot send command %s ' % command


try:
    SERIAL = serial.Serial(Constants.serial_device, 9600)
except OSError:
    print 'Unable to open %s' % Constants.serial_device


def main():
    input_queue = Queue()
    output_queue = Queue()

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
