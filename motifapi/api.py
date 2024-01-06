from __future__ import print_function
import re
import json
import ssl
import socket
import os.path
import subprocess
import logging

from six.moves import urllib, http_client

DEFAULT_HTTP_TIMEOUT = 10  # seconds


# http://code.activestate.com/recipes/577548-https-httplib-client-connection-with-certificate-v/
# http://stackoverflow.com/questions/1875052/using-paired-certificates-with-urllib2

class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
    """
    Allows sending a client certificate with the HTTPS connection.
    This version also validates the peer (server) certificate since, well...
    """

    def __init__(self, key=None, cert=None, ca_certs=None, ssl_version=None):
        urllib.request.HTTPSHandler.__init__(self)
        self.key = key
        self.cert = cert
        self.ca_certs = ca_certs
        self.ssl_version = ssl_version

    def https_open(self, req):
        # Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.get_connection, req)

    def get_connection(self, host, timeout=DEFAULT_HTTP_TIMEOUT):
        return HTTPSConnection(host,
                               key_file=self.key,
                               cert_file=self.cert,
                               timeout=timeout,
                               ca_certs=self.ca_certs,
                               ssl_version=self.ssl_version)


class HTTPSConnection(http_client.HTTPSConnection):
    """
    Overridden to allow peer certificate validation, configuration
    of SSL/ TLS version.  See:
    http://hg.python.org/cpython/file/c1c45755397b/Lib/httplib.py#l1144
    and `ssl.wrap_socket()`
    """

    def __init__(self, host, **kwargs):
        self.ca_certs = kwargs.pop('ca_certs', None)
        self.ssl_version = kwargs.pop('ssl_version', ssl.PROTOCOL_SSLv23)

        http_client.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)

        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = ssl.wrap_socket(sock,
                                    keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    ca_certs=self.ca_certs,
                                    cert_reqs=ssl.CERT_REQUIRED if self.ca_certs else ssl.CERT_NONE,
                                    ssl_version=self.ssl_version)


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

    API = {'version$': 'GET',
           'cameras$': 'GET',
           'cameras/configure$': 'PATCH',
           'cameras/read/(?P<name>[^\s /]+)$': 'GET',
           'camera/(?P<serial>[^\s /]+)$': 'GET',
           'camera/(?P<serial>[^\s /]+)/configure$': 'PATCH',
           'camera/(?P<serial>[^\s /]+)/read/(?P<name>[^\s /]+)$': 'GET',
           'camera/(?P<serial>[^\s /]+)/recording/start$': 'POST',
           'camera/(?P<serial>[^\s /]+)/recording/stop$': 'POST',
           'camera/(?P<serial>[^\s /]+)/recordings$': 'GET',
           'camera/(?P<serial>[^\s /]+)/recordings/copy_all$': 'POST',
           'camera/(?P<serial>[^\s /]+)/recordings/export_all$': 'POST',
           'camera/(?P<serial>[^\s /]+)/io/(?P<name>[^\s /]+)/set': 'POST',
           'camera/(?P<serial>[^\s /]+)/io/log': 'POST',
           'camera/(?P<serial>[^\s /]+)/io/read': 'GET',
           'recording/start$': 'POST',
           'recording/stop$': 'POST',
           'recordings$': 'GET',
           'recordings/copy_all$': 'POST',
           'recordings/export_all$': 'POST',
           'schedule$': 'GET',
           'schedule/clear$': 'POST',
           'schedule/(?P<identifier>[^\s /]+)/clear$': 'DELETE',
           'schedule/recording/start$': 'POST',
           'schedule/camera/(?P<serial>[^\s /]+)/recording/start$': 'POST',
           'schedule/recordings/copy_all': 'POST',
           'schedule/camera/(?P<serial>[^\s /]+)/recordings/copy_all$': 'POST',
           'schedule/recordings/export_all': 'POST',
           'schedule/camera/(?P<serial>[^\s /]+)/recordings/export_all$': 'POST',
           'schedule/io/(?P<name>[^\s /]+)/set': 'POST',
           'schedule/camera/(?P<serial>[^\s /]+)/io/(?P<name>[^\s /]+)/set': 'POST',
           'schedule/cameras/configure/(?P<name>[^\s /]+)': 'POST',
           'schedule/camera/(?P<serial>[^\s /]+)/configure/(?P<name>[^\s /]+)': 'POST',
           'io/(?P<io_serial>[^\s /]+)/(?P<io_port>[^\s /]+)/set': 'POST',
           'io/(?P<name>[^\s /]+)/set': 'POST',
           'io/log': 'POST',
           'io/read': 'GET',
           'multicam/synchronize': 'POST',
           'multicam/connect_camera/(?P<serial>[^\s /]+)': 'POST',
           'multicam/disconnect_camera/(?P<serial>[^\s /]+)': 'POST',
           'multicam/connect_all': 'POST',
           'multicam/disconnect_all': 'POST',
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
            ca_certs=ca_cert,
            ssl_version=ssl.PROTOCOL_SSLv23)
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



