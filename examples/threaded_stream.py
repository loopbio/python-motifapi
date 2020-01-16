import threading
import time
import cv2

from motifapi import MotifApi



class LatestImage(threading.Thread):

    daemon = True

    def __init__(self, api):
        super(LatestImage, self).__init__()

        self._img = self._ts = None
        self._lock = threading.Lock()

        self._stream = api.get_stream(stream_type=MotifApi.STREAM_TYPE_IMAGE)
        assert self._stream is not None

    def run(self):
        while True:
            I, md = self._stream.get_next_image()
            with self._lock:
                self._img = I.copy()
                self._ts = md['timestamp']

    @property
    def latest_image(self):
        with self._lock:
            if self._img is not None:
                print time.time() - self._ts
                return self._img.copy()


def slow_thing(I):
    time.sleep(0.1)
    cv2.imshow('live', I)
    cv2.waitKey(1)



if __name__ == "__main__":
    api = MotifApi(None, None)

    poller = LatestImage(api)
    poller.start()

    while True:
        I = poller.latest_image
        if I is not None:
            slow_thing(I)


