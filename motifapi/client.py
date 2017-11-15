from __future__ import print_function
import re
import json
import ssl
import socket
import os.path
import subprocess

from six.moves import urllib, http_client

DEFAULT_HTTP_TIMEOUT = 10 #seconds

# http://code.activestate.com/recipes/577548-https-httplib-client-connection-with-certificate-v/
# http://stackoverflow.com/questions/1875052/using-paired-certificates-with-urllib2

class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
    '''
    Allows sending a client certificate with the HTTPS connection.
    This version also validates the peer (server) certificate since, well...
    '''
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
        return HTTPSConnection( host, 
                key_file = self.key, 
                cert_file = self.cert,
                timeout = timeout,
                ca_certs = self.ca_certs, 
                ssl_version = self.ssl_version )


class HTTPSConnection(http_client.HTTPSConnection):
    '''
    Overridden to allow peer certificate validation, configuration
    of SSL/ TLS version.  See:
    http://hg.python.org/cpython/file/c1c45755397b/Lib/httplib.py#l1144
    and `ssl.wrap_socket()`
    '''
    def __init__(self, host, **kwargs):
        self.ca_certs = kwargs.pop('ca_certs',None)
        self.ssl_version = kwargs.pop('ssl_version',ssl.PROTOCOL_SSLv23)

        http_client.HTTPSConnection.__init__(self,host,**kwargs)

    def connect(self):
        sock = socket.create_connection( (self.host, self.port), self.timeout )

        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = ssl.wrap_socket( sock, 
                keyfile = self.key_file, 
                certfile = self.cert_file,
                ca_certs = self.ca_certs,
                cert_reqs = ssl.CERT_REQUIRED if self.ca_certs else ssl.CERT_NONE,
                ssl_version = self.ssl_version )


class MethodRequest(urllib.request.Request):
    'See: https://gist.github.com/logic/2715756'
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return self._method if self._method is not None else urllib.request.Request.get_method(self, *args, **kwargs)


class APIError(Exception):
    def __init__(self, message, code):
        self.code = code
        Exception.__init__(self, message)


class Motif(object):

    API = {'version$': 'GET',
           'cameras$': 'GET',
           'cameras/configure$': 'PATCH',
           'camera/(?P<serial>[^\s /]+)$': 'GET',
           'camera/(?P<serial>[^\s /]+)/configure$': 'PATCH',
           'camera/(?P<serial>[^\s /]+)/recording/start$': 'POST',
           'camera/(?P<serial>[^\s /]+)/recording/stop$': 'POST',
           'camera/(?P<serial>[^\s /]+)/recordings$': 'GET',
           'recording/start$': 'POST',
           'recording/stop$': 'POST',
           'recordings$': 'GET',
    }

    def __init__(self, host, api_key, port=6083, ca_cert=None):
        if (host is None) and (api_key is None):
            host = '127.0.0.1'
            try:
                api_key = subprocess.check_output(['recnode-apikey']).strip()
            except OSError:
                raise ValueError('API key must be specified')

        if ca_cert is None:
            ca_cert = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'server.crt')

        if not os.path.exists(ca_cert):
            raise ValueError('could not find certificate: %s' % ca_cert)

        client_cert_key = None
        client_cert_pem = None #file path 
        handler = HTTPSClientAuthHandler( 
            key = client_cert_key,
            cert = client_cert_pem,
            ca_certs = ca_cert,
            ssl_version = ssl.PROTOCOL_SSLv23)
        self._http = urllib.request.build_opener(handler)

        self._host = host
        self._api_key = api_key
        self._port = port

    def _build_request(self, endpoint, data=None, method='GET'):
        if endpoint[0] == '/':
            endpoint = endpoint[1:]
        if data is not None:
            data = json.dumps(data)
        req = MethodRequest('https://%s:%s/%s' % (self._host, self._port, endpoint), data, method=method)
        req.add_header('X-Api-Key', self._api_key)
        req.add_header('Content-Type', 'application/json')
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
                err = json.loads(raw)
                exc = APIError(err['error'], err['status_code'])
            except Exception:
                raise ValueError('unknown API error')
            raise exc

    def call(self, endpoint, method=None, data=None, **kwargs):
        meth = ep = None
        for _ep, _meth in self.API.items():
            if re.match(_ep, endpoint):
                meth = _meth
                ep = _ep
                break

        if meth is None:
            raise ValueError('unknown endpoint')

        req = self._build_request(endpoint,
                                  data=kwargs or None,
                                  method=meth)
        out = self._call(req)
        if out:
            try:
                return json.loads(out)
            except ValueError as e:
                raise ValueError('Invalid JSON response: %s' % e.message)
        else:
            return {}

