from boto.sqs.message import RawMessage
from constants import Constants
import boto.sqs
import threading


class ExternalQueueReaderThread(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        sqs = boto.sqs.connect_to_region(
            Constants.aws_region,
            aws_access_key_id=Constants.aws_access_key,
            aws_secret_access_key=Constants.aws_secret_key)
        self.remote_queue = sqs.get_queue(Constants.aws_sqs_queue_name)
        self.remote_queue.set_message_class(RawMessage)

    def run(self):
        while True:
            messages = self.remote_queue.get_messages(10, None, None, 20)

            for message in messages:
                body = message.get_body()
                print 'Received message from remote queue: %s' % body
                try:
                    room, value = body.split('/', 1)
                    self.queue.put((room, value))
                except ValueError:
                    print 'Unable to process message: %s' % body
                self.remote_queue.delete_message(message)
