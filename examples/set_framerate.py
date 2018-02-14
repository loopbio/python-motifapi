from __future__ import print_function

import logging
logging.basicConfig(level=logging.DEBUG)

from motifapi import MotifApi

# You need to fill these out
IP_ADDRESS = None
API_KEY = None

api = MotifApi(IP_ADDRESS, API_KEY)

# set the serial number of the first started camera
camsn = api.call('cameras')['cameras'][0]['serial']
print(api.call('camera/%s' % camsn))

# set that camera to 5 fps
api.call('camera/%s/configure' % camsn, AcquisitionFrameRate=5.0)
