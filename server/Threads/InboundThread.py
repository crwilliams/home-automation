from process_zway_log import set_lights
import threading


class InboundThread(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue

    def run(self):
        while True:
            event = self.queue.get(True)
            set_lights(event[0], event[1])
