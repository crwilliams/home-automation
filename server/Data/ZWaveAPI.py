import urllib2

from constants import Constants


class ZWaveAPI(object):
    def __init__(self):
        self._host = '127.0.0.1'
        self._port = '8083'
        self._path = 'ZWaveAPI/Run/'

    def get(self, device, instance, command_class):
        url = 'http://%s:%s/%sdevices[%s].instances[%s].%s.Get()' % (
            self._host, self._port, self._path, device, instance, command_class)
        urllib2.urlopen(url)

    def set(self, device, instance, command_class, value):
        url = 'http://%s:%s/%sdevices[%s].instances[%s].%s.Set(%s)' % (
            self._host, self._port, self._path, device, instance, command_class,
            value)
        urllib2.urlopen(url)

    def set_lights(self, room, action):
        if room in Constants.config.keys():
            device = Constants.config[room]
        else:
            return False

        if device[2] == 'SwitchMultilevel' or device[2] == 'SwitchBinary':
            action = get_valid_action(action)

            if action is not None:
                self.set(device[0], device[1], device[2], action)
                return True
            else:
                return False


def get_valid_action(action):
    if action == 'on':
        action = 255
    elif action == 'off':
        action = 0

    action = int(action)

    if action == 255 or 0 <= action <= 100:
        return action
    else:
        return None
