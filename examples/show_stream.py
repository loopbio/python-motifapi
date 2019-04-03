import cv2

from motifapi import MotifApi
api = MotifApi(None, None)

stream = api.get_stream()
if stream is not None:
    while True:
        I, md = stream.get_next_image()
        cv2.imshow('live', I)
        cv2.waitKey(1)

