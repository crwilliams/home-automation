import json
import threading

import boto.sns

from constants import Constants


class OutboundThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self._queue = queue

    def run(self):
        while True:
            message = self._queue.get(True)
            send_push(message[0], message[1], message[2], message[3])


def send_push(room, value, room_type, timestamp):
    print 'Sending push notification for %s: %s (at time %s)' % (
        room, value, timestamp)

    sns = boto.sns.connect_to_region(
        Constants.aws_region,
        aws_access_key_id=Constants.aws_access_key,
        aws_secret_access_key=Constants.aws_secret_key)
    json_string = json.dumps({
        'default': ' '.join([room, value]),
        'GCM': json.dumps({'data': {
            'room': room, 'value': value, 'type': room_type,
            'time': timestamp}
        })
    })
    sns.publish(
        Constants.aws_sns_topic,
        json_string,
        message_structure='json')
