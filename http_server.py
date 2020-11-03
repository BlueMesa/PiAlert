"""An example HTTP server with GET and POST endpoints."""

from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import json


class _RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))
        print(message)
        self._set_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))


def run_server():
    server_address = ('', 8001)
    httpd = HTTPServer(server_address, _RequestHandler)
    print('serving at %s:%d' % server_address)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
