from constants import Constants
from process_zway_log import State
import math
import threading
import time


class TimerThread(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue

    def run(self):
        while True:
            for name, limit in Constants.limits.iteritems():
                try:
                    room = State().rooms[name]
                    try:
                        value = int(room.get_value())
                    except TypeError:
                        value = 0
                    except ValueError:
                        value = 0
                    if value > 0:
                        duration = int(
                            math.floor((time.time() - room.get_time())/60.0))
                        if duration > limit:
                            self.queue.put((name, 0))
                except ValueError:
                    pass
            time.sleep(60)
