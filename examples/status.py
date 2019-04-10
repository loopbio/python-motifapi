import time
import pprint

from motifapi import MotifApi, MotifError
api = MotifApi(None, None)

while 1:
    try:
        resp = api.call('cameras')
        for c in resp.get('cameras'):
            pprint.pprint(api.call('camera/%s' % c['serial']))
    except MotifError:
        pass
    time.sleep(2)

