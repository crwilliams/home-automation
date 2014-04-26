import threading

from Data.State import State


class InboundThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self._queue = queue

    def run(self):
        while True:
            event = self._queue.get(True)
            State().zwave_api.set_lights(event[0], event[1])
