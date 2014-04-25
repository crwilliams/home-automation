import threading
import time

from constants import Constants
from Data.State import State


class TimerThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self._queue = queue

    def run(self):
        while True:
            for name, limit in Constants.limits.iteritems():
                try:
                    room = State().rooms[name]
                    if room.is_on() and room.get_duration() > limit:
                        self._queue.put((name, 0))
                except ValueError:
                    pass
            time.sleep(60)
