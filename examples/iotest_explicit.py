from __future__ import print_function

import time
import random
import logging
logging.basicConfig(level=logging.DEBUG)

from motifapi import MotifApi

# You need to fill these out
IP_ADDRESS = None
API_KEY = None

api = MotifApi(IP_ADDRESS, API_KEY)

# In single camera mode, with phidgets backend, you can leave the backend
# connection unconfigured and just set its state (0/1) or value (0 - 1)
# explicitly/lazily when required.
#
# This allows easy testing without adjusting the config file
#
# First parameter (-1) is the serial number of the phidget. if you have
# multiple connected, you must set this. Otherwise -1 uses the first
# detected device
#
# the second parameter, '0', is the port the digital output is connected to
#
# you pass state=1 to turn it on, state=0 to turn it off

api.call('io/-1/0/set', state=1)
time.sleep(2)
api.call('io/-1/0/set', state=0)
time.sleep(2)

