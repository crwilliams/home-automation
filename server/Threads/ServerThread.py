from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from xml.sax.saxutils import XMLGenerator
import json
import threading
import os
import random

from constants import Constants
from Data.Room import Room
from Data.State import State


class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        server = HTTPServer(('', 8080), MyHandler)
        print 'started http server...'
        server.serve_forever()


class MyHandler(BaseHTTPRequestHandler):
    def __getattr__(self, name):
        if name == 'do_GET':
            return self.do_get

    def log_message(self, f, *args):
        return

    def do_get(self):
        try:
            path_parts = self.path.lstrip('/').split('/')
            if path_parts[0] == '':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.output_main_page()
            elif path_parts[0] == 'photo':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.output_photo_page()
            elif path_parts[0] == 'photo.jpg':
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.output_random_photo('/home/pi/photoframe/')
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
                if State().zwave_api.set_lights(room, action):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
            return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def output_random_photo(self, path):
        filename = random.choice(os.listdir(path))
        with open(path + filename, 'r') as f:
            self.wfile.write(f.read())

    def output_main_page(self):
        gen = XMLGenerator(self.wfile, 'utf-8')
        gen.startDocument()
        gen.startElement('html', {'lang': 'en'})
        html_generator = HtmlPageGenerator(gen)
        html_generator.output_head()
        html_generator.output_body()
        gen.endElement('html')
        gen.endDocument()

    def output_photo_page(self):
        gen = XMLGenerator(self.wfile, 'utf-8')
        gen.startDocument()
        gen.startElement('html', {'lang': 'en'})
        html_generator = HtmlPhotoPageGenerator(gen)
        html_generator.output_head()
        html_generator.output_body()
        gen.endElement('html')
        gen.endDocument()


class HtmlPageGenerator(object):
    def __init__(self, xml_generator):
        self.gen = xml_generator

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
            try:
                self.output_row(
                    room, Constants.values[room_config[2]])
            except KeyError:
                pass

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
        if len(actions):
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


class HtmlPhotoPageGenerator(object):
    def __init__(self, xml_generator):
        self.gen = xml_generator

    def output_head(self):
        self.gen.startElement('head', {})
        self.output_title(Constants.web_page_title)
        self.output_scripts()
        self.output_stylesheet()
        self.gen.endElement('head')

    def output_body(self):
        self.gen.startElement('body', {
            'onload': 'startup()',
            'onclick': 'openForm()',
            'style': 'text-align: center; background-color: black',
        })
        self.gen.startElement('img', {
            'id': 'photo',
            'src': '/photo.jpg',
            'style': 'height: 100%;',
        })
        self.gen.endElement('img')
        self.gen.startElement('form', {})
        self.gen.startElement('table', {
            'id': 'lights',
            'style': 'position: absolute; top: 0px; left: 0px;',
        })

        for room, room_config in Constants.config.iteritems():
            try:
                self.output_row(
                    room, Constants.values[room_config[2]])
            except KeyError:
                pass

        self.gen.startElement('tr', {})
        self.gen.startElement('td', {
            'colspan': '3',
        })
        self.gen.startElement('input', {
            'type': 'button',
            'value': 'dim',
            'onclick': 'dim(); event.stopPropagation();',
            'style': 'width: 10%;',
        })
        self.gen.startElement('input', {
            'type': 'button',
            'value': 'close',
            'onclick': 'closeForm(); event.stopPropagation();',
            'style': 'width: 90%;',
        })
        self.gen.endElement('input')
        self.gen.endElement('td')
        self.gen.endElement('tr')
        self.gen.endElement('table')
        self.gen.endElement('form')

        self.gen.endElement('body')

    def output_title(self, title):
        self.gen.startElement('title', {})
        self.gen.characters(title)
        self.gen.endElement('title')

    def output_stylesheet(self):
        self.gen.startElement('style', {})
        self.gen.characters("""
body {
    padding: 0;
    margin: 0;
    overflow: hidden;
}
table {
    font-family: Arial;
    font-size: 1.5em;
    padding: 0.5em;
    margin: 0;
    background-color: black;
    color: white;
    opacity: 0.8;
}
input {
    font-size: 1em;
    color: gray;
    background-color: black;
    height: 100%;
    width: 3em;
}
body, table {
    width: 100%;
    height: 100%;
}
img {
    margin: 0;
    padding: 0;
}
""")
        self.gen.endElement('style')

    def output_row(self, room, actions):
        action_map = {
            'on': 'on',
            'off': 'off',
            '30': 'l',
            '60': 'm',
            '90': 'h',
        }
        if len(actions):
            self.gen.startElement('tr', {})
            self.gen.startElement('td', {})
            self.gen.characters(room[0].upper() + room[1:].lower())
            self.gen.endElement('td')
            self.gen.startElement('td', {
                'style': 'text-align: right;',
            })
            for action in actions:
                if action_map.has_key(action):
                    self.output_button(room, action_map[action], action)
            self.gen.endElement('td')
            self.gen.endElement('tr')

    def output_button(self, room, action_name, action):
        self.gen.startElement('input', {
            'type': 'button',
            'id': '%s-%s' % (room, action_name),
            'value': action_name.upper(),
            'onclick': 'set("%s", "%s"); event.stopPropagation();' % (room, action)})
        self.gen.endElement('input')

    def output_scripts(self):
        self.gen.startElement('script', {})
        self.gen.characters("""
function httpGet(theUrl, callback, postprocess) {
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
    if (callback !== undefined) {
        xmlHttp.onreadystatechange = alertContents;
    }
    xmlHttp.open("GET", theUrl);
    xmlHttp.send();

    function alertContents() {
        if (xmlHttp.readyState === 4) {
            if (xmlHttp.status === 200) {
                callback(xmlHttp.responseText, postprocess);
            }
        }
    }
};

function set(room, mode)
{
    httpGet('/lights/' + room + '/' + mode);
}

function openForm()
{
    document.getElementById('photo').style.display = 'block';
    checkStatus(actuallyOpenForm);
}

function actuallyOpenForm()
{
    document.getElementById('lights').style.display = 'block';
}

function dim()
{
    document.getElementById('photo').style.display = 'none';
    closeForm();
}

function closeForm()
{
    document.getElementById('lights').style.display = 'none';
}

function updatePhoto()
{
    var photo = document.getElementById('photo');
    if(photo.style.display == 'block')
    {
        photo.src = '/photo.jpg/' + new Date().getTime();
    }
}

function startup()
{
    closeForm();
    setInterval(updatePhoto, 5000);
}

function checkStatus(postprocess)
{
    httpGet('/data', process, postprocess);

    function process(response, postprocess) {
        var json = JSON.parse(response);
        for(var i in json['rooms']) {
            var onButton = document.getElementById(i + '-on');
            var offButton = document.getElementById(i + '-off');
            if (json['rooms'][i] == '0' || json['rooms'][i] == 'False') {
                if (onButton != null) {
                    onButton.style.color = 'gray';
                    onButton.style.backgroundColor = 'black';
                }
                if (offButton != null) {
                    offButton.style.color = 'white';
                    offButton.style.backgroundColor = 'darkred';
                }
            } else if (json['rooms'][i] != null) {
                if (onButton != null) {
                    onButton.style.color = 'white';
                    onButton.style.backgroundColor = 'darkgreen';
                }
                if (offButton != null) {
                    offButton.style.color = 'gray';
                    offButton.style.backgroundColor = 'black';
                }
            }
        }
        if (postprocess !== undefined) {
            postprocess();
        }
        if (document.getElementById('lights').style.display == 'block') {
            setTimeout(checkStatus, 1000);
        }
    }
}
""")
        self.gen.endElement('script')


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, State):
            return obj.get_dict()
        if isinstance(obj, Room):
            return obj.get_value()
        return json.JSONEncoder.default(self, obj)
