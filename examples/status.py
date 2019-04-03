import time
import pprint
import urllib2

from motifapi import MotifApi, MotifApiError
api = MotifApi(None, None)

while 1:
    try:
        resp = api.call('cameras')
        for c in resp.get('cameras'):
            pprint.pprint(api.call('camera/%s' % c['serial']))
    except urllib2.URLError:
        # not running
        pass
    except MotifApiError:
        # camera starting/stopping/race
        pass
    time.sleep(2)

