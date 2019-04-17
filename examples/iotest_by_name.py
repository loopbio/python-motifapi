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

# demonstrates how to set the value of an IO output which has been configured
# in the backend by name
#
# i.e. in this example there is one LED Output configured

api.call('io/led/set', value=random.random())
