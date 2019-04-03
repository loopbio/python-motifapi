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

