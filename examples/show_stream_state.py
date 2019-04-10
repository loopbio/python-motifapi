import cv2

from motifapi import MotifApi
api = MotifApi(None, None)

stream = api.get_stream(stream_type=MotifApi.STREAM_TYPE_STATE)
if stream is not None:
    while True:
        print stream.get_next_state()

