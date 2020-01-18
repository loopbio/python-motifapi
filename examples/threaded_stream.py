from __future__ import print_function

import threading
import time
import cv2

from motifapi import MotifApi



class LatestImage(threading.Thread):

    daemon = True

    def __init__(self, api):
        super(LatestImage, self).__init__()

        self._img = self._md = None
        self._lock = threading.Lock()

        self._stream = api.get_stream(stream_type=MotifApi.STREAM_TYPE_IMAGE)
        assert self._stream is not None

    def run(self):
        while True:
            I, md = self._stream.get_next_image(copy=False)
            with self._lock:
                self._img = I.copy()
                self._md = md.copy()

    @property
    def latest_image(self):
        with self._lock:
            if self._img is not None:
                return self._img, self._md


def slow_thing(I, md):
    time.sleep(0.1)
    cv2.imshow('live', I)
    cv2.waitKey(1)



if __name__ == "__main__":
    api = MotifApi(None, None)

    poller = LatestImage(api)
    poller.start()

    while True:
        latest = poller.latest_image
        if latest is not None:
            slow_thing(*latest)


