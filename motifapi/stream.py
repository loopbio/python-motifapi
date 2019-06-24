import json
import threading

import zmq
import numpy as np


def recv_array(socket, flags=0, copy=True, track=False):
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = np.frombuffer(buf, dtype=md.pop('dtype'))
    return A.reshape(md.pop('shape')), md


class ImageStreamer(object):

    stream = None

    def __init__(self, host, port):
        ctx = zmq.Context()
        address = "tcp://%s:%d" % (host, port)
        sock = ctx.socket(zmq.PULL)
        sock.bind(address)
        self.stream = sock

    def get_next_image(self, block=True):
        while True:
            while self.stream.poll(0, zmq.POLLIN):
                return recv_array(self.stream)
            if not block:
                return None, None


class StateStreamer(object):

    def __init__(self, host, port, channel='j'):
        ctx = zmq.Context()
        address = "tcp://%s:%d" % (host, port)
        sock = ctx.socket(zmq.SUB)
        sock.connect(address)
        sock.setsockopt(zmq.LINGER, 0)
        sock.setsockopt(zmq.SUBSCRIBE, channel)
        self.stream = sock

    def get_next_state(self, block=True):
        while True:
            _, msg = self.stream.recv_multipart()
            return json.loads(msg)


class StateMirror(threading.Thread):

    daemon = True

    def __init__(self, streamer):
        assert isinstance(streamer, StateStreamer)
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self._state = {}
        self._streamer = streamer

    @property
    def is_recording(self):
        return self._state.get('is_recording', False)

    @property
    def frame_number(self):
        return self._state.get('frame_number', None)

    @property
    def frame_time(self):
        return self._state.get('frame_time', None)

    def get_state(self, **extra):
        with self._lock:
            extra.update(self._state)
            return extra

    def run(self):
        while True:
            _, msg = self._streamer.stream.recv_multipart()
            with self._lock:
                self._state.update(json.loads(msg))
