#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from services import get_services_from_kubectl

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=script_dir, **kwargs)

    def do_GET(self):
        if self.path == '/api/health':
            self.send_health_response()
        elif self.path == '/services.json':
            self.send_services()
        else:
            super().do_GET()

    def send_health_response(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'status': 'healthy', 'service': 'startpage'}
        self.wfile.write(json.dumps(response).encode())

    def send_services(self):
        """Status endpoint with more details"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(get_services_from_kubectl()).encode())

def main():
    port = int(os.environ.get('PORT', 8000))
    server_address = ('', port)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    httpd = HTTPServer(server_address, CustomHandler)
    print(f'Starting server on port {port}...')
    print(f'Serving files from: {script_dir}')
    print(f'Custom endpoints: /api/health, /api/status')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        httpd.shutdown()

if __name__ == '__main__':
    main()