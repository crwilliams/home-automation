from collections import defaultdict

from Room import Room
from ZWaveAPI import ZWaveAPI


class State(object):
    _instance = None
    rooms = None
    day_or_night = None
    log = None
    zwave_api = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(State, cls).__new__(cls)
            print 'creating singleton'
            cls._instance.rooms = defaultdict(Room)
            cls._instance.log = []
            cls._instance.zwave_api = ZWaveAPI()
        return cls._instance

    def get_dict(self):
        return {
            'rooms': dict(self.rooms),
            'day_or_night': self.day_or_night,
        }

    def add_log_entry(self, timestamp, room, value):
        self.log.append({'time': timestamp, 'room': room, 'value': value})
