import re
import json
import ssl
import socket
import os.path
import subprocess
import logging
import urllib.request
import urllib.error
import http.client

DEFAULT_HTTP_TIMEOUT = 10  # seconds


# http://code.activestate.com/recipes/577548-https-httplib-client-connection-with-certificate-v/
# http://stackoverflow.com/questions/1875052/using-paired-certificates-with-urllib2

class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
    """
    Allows sending a client certificate with the HTTPS connection.
    This version also validates the peer (server) certificate.
    """

    def __init__(self, key=None, cert=None, ca_certs=None):
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ctx.check_hostname = False
        if ca_certs:
            self.ctx.verify_mode = ssl.CERT_REQUIRED
            self.ctx.load_verify_locations(ca_certs)
        else:
            self.ctx.verify_mode = ssl.CERT_NONE
        if cert:
            self.ctx.load_cert_chain(cert, key)
        urllib.request.HTTPSHandler.__init__(self, context=self.ctx)

    def https_open(self, req):
        return self.do_open(self.get_connection, req)

    def get_connection(self, host, timeout=DEFAULT_HTTP_TIMEOUT):
        return HTTPSConnection(host, timeout=timeout, context=self.ctx)


class HTTPSConnection(http.client.HTTPSConnection):
    """
    Overridden to allow peer certificate validation using an SSLContext.
    """

    def __init__(self, host, **kwargs):
        self.ctx = kwargs.pop('context', None)
        http.client.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)

        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        if self.ctx:
            self.sock = self.ctx.wrap_socket(sock, server_hostname=self.host)
        else:
            self.sock = sock


class MethodRequest(urllib.request.Request):
    # See: https://gist.github.com/logic/2715756

    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return self._method if self._method is not None else urllib.request.Request.get_method(self, *args, **kwargs)


class MotifError(Exception):
    pass


class MotifApiError(MotifError):
    def __init__(self, message, code):
        self.code = code
        Exception.__init__(self, message)


class MotifApi(object):

    STREAM_TYPE_IMAGE = 1
    STREAM_TYPE_STATE = 2

    API = {r'version$': 'GET',
           r'cameras$': 'GET',
           r'cameras/configure$': 'PATCH',
           r'cameras/read/(?P<name>[^\s /]+)$': 'GET',
           r'camera/(?P<serial>[^\s /]+)$': 'GET',
           r'camera/(?P<serial>[^\s /]+)/configure$': 'PATCH',
           r'camera/(?P<serial>[^\s /]+)/read/(?P<name>[^\s /]+)$': 'GET',
           r'camera/(?P<serial>[^\s /]+)/recording/start$': 'POST',
           r'camera/(?P<serial>[^\s /]+)/recording/stop$': 'POST',
           r'camera/(?P<serial>[^\s /]+)/recordings$': 'GET',
           r'camera/(?P<serial>[^\s /]+)/recordings/copy_all$': 'POST',
           r'camera/(?P<serial>[^\s /]+)/recordings/export_all$': 'POST',
           r'camera/(?P<serial>[^\s /]+)/io/(?P<name>[^\s /]+)/set': 'POST',
           r'camera/(?P<serial>[^\s /]+)/io/log': 'POST',
           r'camera/(?P<serial>[^\s /]+)/io/read': 'GET',
           r'recording/start$': 'POST',
           r'recording/stop$': 'POST',
           r'recordings$': 'GET',
           r'recordings/copy_all$': 'POST',
           r'recordings/export_all$': 'POST',
           r'schedule$': 'GET',
           r'schedule/clear$': 'POST',
           r'schedule/(?P<identifier>[^\s /]+)/clear$': 'DELETE',
           r'schedule/recording/start$': 'POST',
           r'schedule/camera/(?P<serial>[^\s /]+)/recording/start$': 'POST',
           r'schedule/recordings/copy_all': 'POST',
           r'schedule/camera/(?P<serial>[^\s /]+)/recordings/copy_all$': 'POST',
           r'schedule/recordings/export_all': 'POST',
           r'schedule/camera/(?P<serial>[^\s /]+)/recordings/export_all$': 'POST',
           r'schedule/io/(?P<name>[^\s /]+)/set': 'POST',
           r'schedule/camera/(?P<serial>[^\s /]+)/io/(?P<name>[^\s /]+)/set': 'POST',
           r'schedule/cameras/configure/(?P<name>[^\s /]+)': 'POST',
           r'schedule/camera/(?P<serial>[^\s /]+)/configure/(?P<name>[^\s /]+)': 'POST',
           r'io/(?P<io_serial>[^\s /]+)/(?P<io_port>[^\s /]+)/set': 'POST',
           r'io/(?P<name>[^\s /]+)/set': 'POST',
           r'io/log': 'POST',
           r'io/read': 'GET',
           r'multicam/synchronize': 'POST',
           r'multicam/connect_camera/(?P<serial>[^\s /]+)': 'POST',
           r'multicam/disconnect_camera/(?P<serial>[^\s /]+)': 'POST',
           r'multicam/connect_all': 'POST',
           r'multicam/disconnect_all': 'POST',
           }

    def __init__(self, host=None, api_key=None, port=None, ca_cert=None, api_version=1):
        self._log = logging.getLogger('motifapi')

        if port is None:
            try:
                port = int(os.environ.get('MOTIF_PORT', 6083))
            except:
                port = 6083
        else:
            port = int(port)

        if host is None:
            try:
                host = os.environ['MOTIF_HOST']
                self._log.debug('took host from environment')
            except KeyError:
                pass
            if not host:
                host = '127.0.0.1'

        if api_key is None:
            try:
                api_key = os.environ['MOTIF_API_KEY']
                self._log.debug('took api_key from environment')
            except KeyError:
                pass
            if not api_key:
                try:
                    api_key = subprocess.check_output(['recnode-apikey']).strip()
                    self._log.debug('took api-key from recnode-apikey subprocess')
                except OSError:
                    pass

        if not api_key:
            raise ValueError('API key must be specified')

        if ca_cert is None:
            ca_cert = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'server.crt')

        if not os.path.exists(ca_cert):
            raise ValueError('could not find certificate: %s' % ca_cert)

        self._prefix = 'api/%d/' % api_version

        client_cert_key = None
        client_cert_pem = None  # file path
        handler = HTTPSClientAuthHandler(
            key=client_cert_key,
            cert=client_cert_pem,
            ca_certs=ca_cert)
        self._http = urllib.request.build_opener(handler)

        self._host = host
        self._api_key = api_key
        self._port = port

    def _build_request(self, endpoint, data=None, method='GET'):
        if endpoint[0] == '/':
            endpoint = endpoint[1:]

        if endpoint != 'version':
            endpoint = self._prefix + endpoint

        if data is not None:
            try:
                data = json.dumps(data).encode("utf-8")
            except TypeError:
                raise ValueError('Arguments must be JSON serializable (they were %r)' % (data,))

        url = 'https://%s:%s/%s' % (self._host, self._port, endpoint)

        req = MethodRequest(url, data, method=method)
        req.add_header('X-Api-Key', self._api_key)
        req.add_header('Content-Type', 'application/json')

        self._log.debug('%s %s (%d bytes %s)' % (method,
                                                 url,
                                                 0 if data is None else len(data),
                                                 type(data)))

        return req

    def _call(self, req):
        try:
            resp = self._http.open(req)
            data = resp.read()
            resp.close()
            return data
        except urllib.error.HTTPError as e:
            try:
                raw = e.read()
                err = json.loads(raw.decode('utf-8'))
                exc = MotifApiError(err['error'], err['status_code'])
            except Exception:
                raise ValueError('unknown API error')
            raise exc
        except urllib.error.URLError:
            raise MotifError('motif not running or reachable')

    def call(self, endpoint, method=None, data=None, **kwargs):
        meth = ep = None
        for _ep, _meth in self.API.items():
            if re.match(_ep, endpoint):
                meth = _meth
                ep = _ep
                break

        if meth is None:
            raise ValueError("unknown endpoint '%s' (are you missing/adding '/')" % endpoint)

        req = self._build_request(endpoint,
                                  data=kwargs or None,
                                  method=meth)
        out = self._call(req)
        if out:
            try:
                return json.loads(out.decode('utf-8'))
            except ValueError as e:
                raise ValueError('Invalid JSON response: %s' % e.message)
        else:
            return {}

    def is_recording(self, serial):
        r = self.call('camera/%s' % serial)
        if r['camera_info'].get('filename'):
            return True
        elif r['camera_info'].get('status') == 'pending':
            return True
        return False

    def is_copying(self, serial):
        r = self.call('camera/%s' % serial)
        return r['playback_info']['status'] == 'copying'

    def is_exporting(self, serial):
        r = self.call('camera/%s' % serial)
        status = r['playback_info']['status']
        return status.startswith('export') and ('finished' not in status)

    def get_stream(self, serial=None, stream_type=STREAM_TYPE_IMAGE, force_host=None):
        from .stream import ImageStreamer, StateStreamer

        if serial is None:
            try:
                # get the first camera
                for c in self.call('cameras').get('cameras', []):
                    serial = c['serial']
                    break
            except (urllib.error.URLError, MotifApiError):
                raise MotifError('motif not running or reachable')

        if serial is None:
            raise MotifError('no cameras connected or running')

        def _get_host_port(_stream_name):
            _stat = self.call('camera/%s' % serial)
            _host = _stat['camera_info']['stream'][_stream_name]['host']
            _port = int(_stat['camera_info']['stream'][_stream_name]['port'])

            if force_host is not None:
                _host = force_host
            elif (_host == '0.0.0.0') and (self._host != '0.0.0.0'):
                _host = self._host

            return _host, _port

        if stream_type in (MotifApi.STREAM_TYPE_IMAGE, MotifApi.STREAM_TYPE_STATE):
            try:
                if stream_type == MotifApi.STREAM_TYPE_IMAGE:
                    host, port = _get_host_port('image')
                    return ImageStreamer(host, port)
                else:
                    host, port = _get_host_port('state')
                    return StateStreamer(host, port)
            except (urllib.error.URLError, MotifApiError):
                raise MotifError('camera with serial %s not found or running' % serial)
            except KeyError:
                raise MotifError('realtime stream not enabled on camera')
        else:
            raise ValueError('unknown stream type')



