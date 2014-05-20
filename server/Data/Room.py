import math
import time


class Room(object):
    _value = None
    _time = None

    def __repr__(self):
        return str(self._value)

    def update(self, timestamp, value):
        if value.lower() == 'true':
            self._value = True
        elif value.lower() == 'false':
            self._value = False
        else:
            try:
                self._value = int(value)
            except (TypeError, ValueError):
                self._value = None
        self._value = value
        self._time = timestamp

    def get_value(self):
        return self._value

    def get_time(self):
        return self._time

    def is_on(self):
        return (
            (type(self.get_value()) == bool and self.get_value() is True)
            or
            (type(self.get_value()) == int and self.get_value() > 0)
        )

    def is_off(self):
        return not self.is_on()

    def get_duration(self):
        return int(math.floor((time.time() - self.get_time()) / 60.0))