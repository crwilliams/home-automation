class Constants(object):
    aws_region = 'aws-region'  # eg us-east-1
    aws_access_key = 'aws-access-key'
    aws_secret_key = 'aws-secret-key'
    aws_sqs_queue_name = 'sqs-queue-name'
    aws_sns_topic = 'arn:aws:sns:region:project-id:sns-topic-name'
    serial_device = '/dev/ttyUSB0'
    jquery_base_url = 'http://server-hostname/path/jquery/js'
    bootstrap_base_url = 'http://server-hostname/path/bootstrap'
    web_page_title = 'My Lights'
    config = {
        # room-name: (device, instance, type)
        'bedroom1': (2, 0, 'SwitchMultilevel'),
        'bedroom2': (3, 0, 'SwitchMultilevel'),
        'living': (4, 0, 'SwitchBinary'),
        'kitchen': (5, 0, 'SwitchBinary'),
        'dining': (5, 2, 'SwitchBinary'),
        'pir': (6, 0, None),
        'lamp': ('A', 1, 'HomeEasy'),
        'socket1': ('A', 2, 'HomeEasy'),
        'socket2': ('A', 3, 'HomeEasy'),
    }
    rules = [
        # (trigger-room, trigger-value, response-room, response-value)
        ('pir', 'True', 'lamp', 'on'),
        ('pir', 'False', 'lamp', 'off'),
        ('day_or_night', 'night', 'lamp', 'on'),
        ('day_or_night', 'night', 'lamp', 'off'),
    ]
    limits = {
        'bedroom1': 60,
        'bedroom2': 60,
        'living': 120,
        'kitchen': 60,
        'dining': 120,
    }
    values = {
        'SwitchMultilevel': ['off', 'on', '30', '40', '50', '60', '70', '80'],
        'SwitchBinary': ['off', 'on'],
        'HomeEasy': ['off', 'on'],
        None: [],
    }
    input_log_filename = '/tmp/Z-Way.log'
