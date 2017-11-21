from __future__ import print_function

import time
import tempfile
import logging

from motifapi import Motif

logging.basicConfig(level=logging.DEBUG)

IP_ADDRESS = '10.11.12.13'
API_KEY = 'abcdef123456abcdef123456abcdef12'

api = Motif(IP_ADDRESS, API_KEY)

camera_serial = 'FAKE0'

# list all scheduled tasks
print(api.call('schedule'))

# clear one scheduled task by name
# api.call('schedule/%s/clear' % task_name)

# clear all scheduled tasks
# warning: if you share this recording system with others it will also clear their tasks!
api.call('schedule/clear')

# schedule a recording for 10 seconds at :32 between the hours of 16-17h, every day
api.call('schedule/recording/start', task_name='record_video', cron_expression='09 16-17 * * *',
                                     codec='libx264', duration=10)

# at 17:00 schedule all recordings to be copied to the configured location
api.call('schedule/camera/%s/recordings/copy_all' % camera_serial, task_name='copy_days_videos', cron_expression='11 17 * * *')

