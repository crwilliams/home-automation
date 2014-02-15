from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading
import sys
import re
from collections import defaultdict
import json
import urllib2
import time
from Queue import Queue
import boto.sqs
import boto.sns
import serial
from boto.sqs.message import RawMessage

from xml.sax.saxutils import XMLGenerator

from constants import Constants
import ephem


class ServerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        time.sleep(20)
        State().log_init()
        server = HTTPServer(('', 8080), MyHandler)
        print 'started http server...'
        server.serve_forever()


class OutboundThread(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            message = self.queue.get(True)
            send_push(message[0], message[1], message[2], message[3])


class StandardInputReaderThread(threading.Thread):

    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def process_rules(self, room_name, value):
        for rule in Constants.rules:
            if rule[0] == room_name and rule[1] == value:
                print (
                    rule[0] + ' ' + rule[1] + ' triggers ' +
                    rule[2] + ' ' + rule[3])
                self.in_queue.put((rule[2], rule[3]))

    def run(self):    
        timestamp_format = (
            r'\[(?P<timestamp>\d{4}-\d{2}-\d{2} '
            r'\d{2}:\d{2}:\d{2}\.\d{3})\]')

        pattern = re.compile(
            timestamp_format +
            r' SETDATA ' +
            r'devices\.(?P<device>\d)\.' +
            r'instances\.(?P<instance>\d)\.' +
            r'commandClasses\.(?P<cc>(37|38|48))\.' +
            r'data\.(1\.)?' +
            r'level = (?P<value>(\d+|True|False))'
        )

        rooms = {}
        for room, room_config in Constants.config.iteritems():
            rooms['-'.join([str(room_config[0]), str(room_config[1])])] = room

        while True:
            line = sys.stdin.readline()
            if not line:
                break

            match = pattern.match(line)
            if match:
                match_dict = match.groupdict()
                key = '-'.join([match_dict['device'], match_dict['instance']])
                if key in rooms:
                    room_name = rooms[key]
                    print (
                        match_dict['timestamp'] + ' ' + room_name + ': ' +
                        match_dict['value'] + ' ' + match_dict['cc'])
                    previous_update_time = State().rooms[room_name].time
                    previous_update_value = State().rooms[room_name].value
                    current_update_time = time.mktime(time.strptime(
                        match_dict['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
                    State().rooms[room_name].value = match_dict['value']
                    State().rooms[room_name].time = current_update_time
                    if State().is_init() and (
                            previous_update_value != match_dict['value'] or (
                            current_update_time - previous_update_time) > 10):
                        if room_name == 'philio-fix':
                            philio_fix(match_dict['device'])
                            continue
                        self.process_rules(room_name, match_dict['value'])
                        self.out_queue.put((
                            room_name, match_dict['value'],
                            Constants.config[room_name][2],
                            int(current_update_time)))
                else:
                    print 'Error processing ' + key + ': ' + str(match_dict)


class ExternalQueueReaderThread(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        c = boto.sqs.connect_to_region(
            Constants.aws_region,
            aws_access_key_id=Constants.aws_access_key,
            aws_secret_access_key=Constants.aws_secret_key)
        self.remote_queue = c.get_queue(Constants.aws_sqs_queue_name)
        self.remote_queue.set_message_class(RawMessage)

    def run(self):
        while True:
            rs = self.remote_queue.get_messages(10, None, None, 20)

            for m in rs:
                print 'Received message from remote queue: ' + m.get_body()
                try:
                    room, value = m.get_body().split('/', 1)
                    self.queue.put((room, value))
                except ValueError:
                    print 'Unable to process message: ' + m.get_body()
                self.remote_queue.delete_message(m)


class EphemerisThread(threading.Thread):

    def __init__(self, queue, city):
        threading.Thread.__init__(self)
        self.queue = queue
        
        self.sun = ephem.Sun()
        self.location = ephem.city(city)
        
    def day_or_night(self):
        self.sun.compute()
        nr = self.location.next_rising(self.sun)
        ns = self.location.next_setting(self.sun)
        if(nr < ns):
            return 'night'
        else:
            return 'day'

    def run(self):
        while True:
            new_day_or_night = self.day_or_night()
            if new_day_or_night != State().day_or_night:
                State().day_or_night = new_day_or_night
                print 'day/night state is now ' + new_day_or_night
                for rule in Constants.rules:
                    if rule[0] == 'day_or_night' and rule[1] == new_day_or_night:
                        print (
                            rule[0] + ' ' + rule[1] + ' triggers ' +
                            rule[2] + ' ' + rule[3])
                        self.queue.put((rule[2], rule[3]))
            time.sleep(10)


class State(object):
    
    _instance = None
    rooms = None
    day_or_night = None
    init = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(State, cls).__new__(cls)
            print 'creating singleton'
            cls._instance.rooms = defaultdict(Room)
            cls._instance.init = False
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


class ComplexEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, State):
            return obj.get_dict()
        if isinstance(obj, Room):
            return obj.value
        return json.JSONEncoder.default(self, obj)


class Room(object):

    value = None
    time = None
    
    def __repr__(self):
        return str(self.value)


class MyHandler(BaseHTTPRequestHandler):

    def __getattr__(self, name):
        if name == 'do_GET':
            return self.do_get

    def do_get(self):
        try:
            path_parts = self.path.lstrip('/').split('/')
            if path_parts[0] == '':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.output_main_page()
            elif path_parts[0] == 'data':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(State(), cls=ComplexEncoder))
            elif path_parts[0] == 'lights':
                room = path_parts[1]
                action = path_parts[2]
                if set_lights(room, action):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
            return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def output_main_page(self):
        w = XMLGenerator(self.wfile, 'utf-8')
        w.startDocument()
        w.startElement('html', {'lang': 'en'})
        self.output_head(w)
        self.output_body(w)
        w.endElement('html')
        w.endDocument()

    @staticmethod
    def output_head(w):
        w.startElement('head', {})
        MyHandler.output_title(w, Constants.web_page_title)
        MyHandler.output_meta(
            w, 'viewport', 'width=device-width, initial-scale=1.0')
        MyHandler.output_stylesheet(
            w, Constants.bootstrap_base_url + '/css/bootstrap.min.css')
        MyHandler.output_stylesheet(
            w, Constants.bootstrap_base_url + '/css/bootstrap-theme.min.css')
        w.endElement('head')

    @staticmethod
    def output_body(w):
        w.startElement('body', {})
        w.startElement('form', {})
        w.startElement('table', {})

        for room, room_config in Constants.config.iteritems():
            MyHandler.output_row(w, room, Constants.values[room_config[2]])

        w.endElement('table')
        w.endElement('form')

        MyHandler.output_scripts(w)
        w.endElement('body')

    @staticmethod
    def output_title(w, title):
        w.startElement('title', {})
        w.characters(title)
        w.endElement('title')

    @staticmethod
    def output_meta(w, name, content):
        w.startElement('meta', {'name': name, 'content': content})
        w.endElement('meta')

    @staticmethod
    def output_stylesheet(w, href):
        w.startElement('link', {
            'href': href,
            'rel': 'stylesheet',
            'media': 'screen'})
        w.endElement('link')

    @staticmethod
    def output_row(w, room, actions):
        w.startElement('tr', {})
        w.startElement('td', {})
        w.characters(room)
        w.endElement('td')
        w.startElement('td', {})
        for action in actions:
            MyHandler.output_button(w, room, action)
        w.endElement('td')
        w.endElement('tr')

    @staticmethod
    def output_button(w, room, action):
        w.startElement('button', {
            'type': 'button',
            'id': room + '-' + action,
            'class': 'btn btn-lg',
            'onclick': 'foo(\'' + room + '\', \'' + action + '\')'})
        w.characters(action)
        w.endElement('button')

    @staticmethod
    def output_scripts(w):
        w.startElement('script', {
            'src': Constants.jquery_base_url + '/jquery-1.10.2.min.js'})
        w.endElement('script')
        w.startElement('script', {
            'src': Constants.bootstrap_base_url + '/js/bootstrap.min.js'})
        w.endElement('script')
        w.startElement('script', {})
        w.characters("""
function foo(room, action)
{
    jQuery.get('/lights/' + room + '/' + action);
}

$(document).ready( function() {
    setInterval(function() {
        jQuery.get('/data', null, function(data, textStatus, jqXHR) {
            $('.btn').removeClass('btn-success');
            $('.btn').removeClass('btn-danger');
            for(var room in data.rooms) {
                if (data.rooms[room] == 0) {
                    var btn = $('#' + room + '-off');
                    if (btn) {
                        btn.addClass('btn-danger');
                    }
                } else {
                    var btn = $('#' + room + '-on');
                    if (btn) {
                        btn.addClass('btn-success');
                    }
                }
            }
        }, 'json');
    }, 1000);
});""")
        w.endElement('script')


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
            url = 'http://127.0.0.1:8083/ZWaveAPI/Run/devices[' + str(
                device[0]) + '].instances[' + str(
                    device[1]) + '].' + device[2] + '.Set(' + str(action) + ')'
            urllib2.urlopen(url)
            return True
        else:
            return False
    elif device[2] == 'HomeEasy':
        command = '-'.join([
            str(device[0]), str(device[1]), str(action.upper())])
        try:
            ser.write(command)
        except NameError:
            print 'No serial device, cannot send command ' + command


def send_push(room, value, room_type, timestamp):
    print (
        'Sending push notification for ' + room + ': ' + value +
        ' (at time ' + str(timestamp) + ')')

    c = boto.sns.connect_to_region(
        Constants.aws_region,
        aws_access_key_id=Constants.aws_access_key,
        aws_secret_access_key=Constants.aws_secret_key)
    json_string = json.dumps({
        'default': room + ' ' + value,
        'GCM': json.dumps({'data': {
            'room': room, 'value': value, 'type': room_type, 'time': timestamp}
        })
    })
    c.publish(
        Constants.aws_sns_topic,
        json_string,
        message_structure='json')


try:
    ser = serial.Serial(Constants.serial_device, 9600)
except OSError:
    print 'Unable to open ' + Constants.serial_device


def main():
    
    ServerThread().start()
    
    input_queue = Queue()
    output_queue = Queue()
    StandardInputReaderThread(input_queue, output_queue).start()
    ExternalQueueReaderThread(input_queue).start()
    OutboundThread(output_queue).start()
    EphemerisThread(input_queue, 'London').start()

    for room, room_config in Constants.config.iteritems():
        if room_config[2] == 'HomeEasy':
            output_queue.put((room, '?', room_config[2], 0))
    
    while True:
        event = input_queue.get(True)
        set_lights(event[0], event[1])


if __name__ == '__main__':
    main()
