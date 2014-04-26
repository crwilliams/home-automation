import re
import sys
import threading
import time

from constants import Constants
from Data.State import State


class InputReaderThread(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self._level_processor = LevelProcessor(in_queue, out_queue)
        self._val_processor = ValProcessor()
        self._input = None

    def run(self):
        while True:
            line = self._input.readline()
            if not line:
                break

            self._process(line)

    def _process(self, line):
        self._level_processor.process(line)
        self._val_processor.process(line)


class FileInputReaderThread(InputReaderThread):
    def __init__(self, in_queue, out_queue, filename):
        InputReaderThread.__init__(self, in_queue, out_queue)
        logfile = open(filename)
        self._input = logfile


class StandardInputReaderThread(InputReaderThread):
    def __init__(self, in_queue, out_queue):
        InputReaderThread.__init__(self, in_queue, out_queue)
        self._input = sys.stdin


class Processor(object):
    def __init__(self):
        self.timestamp_format = (
            r'\[(?P<timestamp>\d{4}-\d{2}-\d{2} '
            r'\d{2}:\d{2}:\d{2}\.\d{3})\]')
        self.pattern = None

    def set_pattern(self, pattern):
        self.pattern = re.compile(pattern)

    def match(self, line):
        return self.pattern.match(line)


class LevelProcessor(Processor):
    def __init__(self, in_queue, out_queue):
        Processor.__init__(self)
        self._in_queue = in_queue
        self._out_queue = out_queue
        self.set_pattern(''.join([
            self.timestamp_format,
            r' SETDATA ',
            r'devices\.(?P<device>\d)\.',
            r'instances\.(?P<instance>\d)\.',
            r'commandClasses\.(?P<cc>(37|38|48))\.',
            r'data\.(1\.)?',
            r'level = (?P<value>(\d+|True|False))'
        ]))
        self.rooms = {}
        for room, room_config in Constants.config.iteritems():
            self.rooms['-'.join([str(x) for x in [
                room_config[0], room_config[1]]])] = room

    def process(self, line):
        match = self.match(line)
        if match:
            match_dict = match.groupdict()
            key = '-'.join([match_dict['device'], match_dict['instance']])
            if key in self.rooms:
                room_name = self.rooms[key]
                print '%s %s: %s %s' % (
                    match_dict['timestamp'], room_name, match_dict['value'],
                    match_dict['cc'])
                previous_time = State().rooms[room_name].get_time()
                previous_value = State().rooms[room_name].get_value()
                current_update_time = time.mktime(time.strptime(
                    match_dict['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
                State().rooms[room_name].update(
                    current_update_time, match_dict['value'])
                if previous_value != match_dict['value'] or (
                        current_update_time - previous_time) > 10:
                    State().add_log_entry(
                        int(current_update_time), room_name,
                        match_dict['value'])
                    if State().is_init():
                        if room_name == 'philio-fix':
                            philio_fix(match_dict['device'])
                            return
                        self._process_rules(room_name, match_dict['value'])
                        self._out_queue.put((
                            room_name, match_dict['value'],
                            Constants.config[room_name][2],
                            int(current_update_time)))
            else:
                print 'Error processing %s: %s' % (key, match_dict)

    def _process_rules(self, room_name, value):
        for rule in Constants.rules:
            if rule[0] == room_name and rule[1] == value:
                print ' '.join([
                    rule[0], rule[1], 'triggers', rule[2], rule[3]])
                self._in_queue.put((rule[2], rule[3]))


class ValProcessor(Processor):
    def __init__(self):
        Processor.__init__(self)
        self.set_pattern(''.join([
            self.timestamp_format,
            r' SETDATA ',
            r'devices\.(?P<device>\d)\.',
            r'instances\.(?P<instance>\d)\.',
            r'commandClasses\.49\.',
            r'data\.(?P<d>\d)\.',
            r'val = (?P<value>([\d\.]+))'
        ]))

    def process(self, line):
        match = self.match(line)
        if match:
            match_dict = match.groupdict()
            update_time = time.mktime(time.strptime(
                match_dict['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
            if int(match_dict['d']) == 1:
                State().add_log_entry(
                    int(update_time), 'temperature', match_dict['value'])
            if int(match_dict['d']) == 5:
                State().add_log_entry(
                    int(update_time), 'humidity', match_dict['value'])


def philio_fix(device):
    for instance in [2, 3]:
        State().zwave_api.get(device, instance, 'commandClasses[37]')
