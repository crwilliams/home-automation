from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from constants import Constants
from process_zway_log import Room, State, set_lights
from xml.sax.saxutils import XMLGenerator
import json
import threading
import time


class ServerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        time.sleep(20)
        State().log_init()
        server = HTTPServer(('', 8080), MyHandler)
        print 'started http server...'
        server.serve_forever()


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
            elif path_parts[0] == 'log':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(State().log, cls=ComplexEncoder))
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
        gen = XMLGenerator(self.wfile, 'utf-8')
        gen.startDocument()
        gen.startElement('html', {'lang': 'en'})
        htmlgen = HtmlPageGenerator(gen)
        htmlgen.output_head()
        htmlgen.output_body()
        gen.endElement('html')
        gen.endDocument()


class HtmlPageGenerator(object):

    def __init__(self, xmlgenerator):
        self.gen = xmlgenerator

    def output_head(self):
        self.gen.startElement('head', {})
        self.output_title(Constants.web_page_title)
        self.output_meta(
            'viewport', 'width=device-width, initial-scale=1.0')
        self.output_stylesheet('%s/css/bootstrap.min.css' % (
            Constants.bootstrap_base_url))
        self.output_stylesheet('%s/css/bootstrap-theme.min.css' % (
            Constants.bootstrap_base_url))
        self.gen.endElement('head')

    def output_body(self):
        self.gen.startElement('body', {})
        self.gen.startElement('form', {})
        self.gen.startElement('table', {})

        for room, room_config in Constants.config.iteritems():
            self.output_row(
                room, Constants.values[room_config[2]])

        self.gen.endElement('table')
        self.gen.endElement('form')

        self.output_scripts()
        self.gen.endElement('body')

    def output_title(self, title):
        self.gen.startElement('title', {})
        self.gen.characters(title)
        self.gen.endElement('title')

    def output_meta(self, name, content):
        self.gen.startElement('meta', {'name': name, 'content': content})
        self.gen.endElement('meta')

    def output_stylesheet(self, href):
        self.gen.startElement('link', {
            'href': href,
            'rel': 'stylesheet',
            'media': 'screen'})
        self.gen.endElement('link')

    def output_row(self, room, actions):
        self.gen.startElement('tr', {})
        self.gen.startElement('td', {})
        self.gen.characters(room)
        self.gen.endElement('td')
        self.gen.startElement('td', {})
        for action in actions:
            self.output_button(room, action)
        self.gen.endElement('td')
        self.gen.endElement('tr')

    def output_button(self, room, action):
        self.gen.startElement('button', {
            'type': 'button',
            'id': '-'.join([room, action]),
            'class': 'btn btn-lg',
            'onclick': 'foo(\'%s\', \'%s\')' % (room, action)})
        self.gen.characters(action)
        self.gen.endElement('button')

    def output_scripts(self):
        self.gen.startElement('script', {
            'src': '%s/jquery-1.10.2.min.js' % Constants.jquery_base_url})
        self.gen.endElement('script')
        self.gen.startElement('script', {
            'src': '%s/js/bootstrap.min.js' % Constants.bootstrap_base_url})
        self.gen.endElement('script')
        self.gen.startElement('script', {})
        self.gen.characters("""
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
        self.gen.endElement('script')


class ComplexEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, State):
            return obj.get_dict()
        if isinstance(obj, Room):
            return obj.get_value()
        return json.JSONEncoder.default(self, obj)
