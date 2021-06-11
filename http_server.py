"""An example HTTP server with GET and POST endpoints."""
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import json
import re

from alerts import AlertHandler
from sensors import SensorReader

sensors = []
alerts_handler = AlertHandler()


class _RequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def _set_not_found(self):
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))
        m = re.search(r'^/sensors/([0-9]+)/reading.json$', self.path)
        sensor_id = int(m.group(1))
        if sensor_id < len(sensors):
            sensor = sensors[sensor_id]
            alerts_handler.handle(sensor, message)
            self._set_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
        else:
            self._set_not_found()



def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, _RequestHandler)
    httpd.address_family = socket.AF_INET6
    print('serving at %s:%d' % server_address)
    httpd.serve_forever()


if __name__ == '__main__':
    sensors = SensorReader.from_yaml('sensors.yml')
    print(sensors)
    run_server()
