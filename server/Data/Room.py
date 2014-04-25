import math
import time


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

    def is_on(self):
        try:
            return int(self.get_value()) > 0
        except (TypeError, ValueError):
            return False

    def get_duration(self):
        return int(math.floor((time.time() - self.get_time()) / 60.0))