from __future__ import print_function
import time
import logging
logging.basicConfig(level=logging.INFO)

from motifapi import MotifApi

# You need to fill these out
IP_ADDRESS = None
API_KEY = None

api = MotifApi(IP_ADDRESS, API_KEY)

# get serial number of first connected camera
camsn = api.call('cameras')['cameras'][0]['serial']

# start recording on one camera
print(api.call('camera/%s/recording/start' % camsn, codec='h264', filename='testing_file',
               metadata={'title': 'test file', 'description': 'a long description'}))
time.sleep(5)
# stop recording on 'all cameras'
print(api.call('camera/%s/recording/stop' % camsn))

# wait for recording to finish (sometimes need to flush the buffer, close video, etc)
while api.is_recording(camsn):
    print('%s still recording' % camsn)
    time.sleep(1)

# in a multi-camera environment you should record to stores as these allow synchronization and
# stitching multiple videos
camera_serials = [cinfo['serial'] for cinfo in api.call('cameras')['cameras']]

# start recording to  on all connected cameras
# record for 10 seconds then stop
print(api.call('recording/start', codec='h264', filename='test_store', duration=10, record_to_store=True,
               metadata={'title': 'test store', 'description': 'a multicamera recording'}))

# wait for all cameras to finish recording
while any(api.is_recording(_sn) for _sn in camera_serials):
    print('still recording %r' % (camera_serials,))
    time.sleep(1)

# list all recordings
print(api.call('recordings'))

# Copy all recordings to the configured storage location
print(api.call('recordings/copy_all', delete_after=True))  # if true, delete files after successful copy
while any(api.is_copying(_sn) for _sn in camera_serials):
    print('still copying')
    time.sleep(1)

print('finished')

