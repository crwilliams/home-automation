import threading
import time

import ephem

from constants import Constants
from process_zway_log import State


class EphemerisThread(threading.Thread):
    def __init__(self, queue, city):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.city = city

    def day_or_night(self):
        sun = ephem.Sun()
        location = ephem.city(self.city)

        sun.compute()
        if location.next_rising(sun) < location.next_setting(sun):
            return 'night'
        else:
            return 'day'

    def run(self):
        while True:
            new_day_or_night = self.day_or_night()
            if new_day_or_night != State().day_or_night:
                State().day_or_night = new_day_or_night
                print 'day/night state is now %s' % new_day_or_night
                for rule in Constants.rules:
                    if (rule[0] == 'day_or_night' and
                            rule[1] == new_day_or_night):
                        print ' '.join([
                            rule[0], rule[1], 'triggers', rule[2], rule[3]])
                        self.queue.put((rule[2], rule[3]))
            time.sleep(10)
