from __future__ import print_function

import time
import random
import logging
logging.basicConfig(level=logging.DEBUG)

from motifapi import MotifApi

IP_ADDRESS = None
API_KEY = None

api = MotifApi(IP_ADDRESS, API_KEY)

# demonstrates how to set the value of IO channels that have been
# configured and are associated with one camera, in a multiple camera
# (index, master, or slave) setup

api.call('camera/FAKE0/io/ledgreen/set', value=random.random())
api.call('camera/FAKE1/io/led/set', value=random.random())
