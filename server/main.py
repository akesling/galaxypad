"""
Basic HTTP server as competition judge server for main app.

This will almost certainly want some more full-featured library once it needs
to do some. For now, no non-standard library dependencies.

Note, if running server on host and app in container, the container must
connect to the host IP (192.168.x.x), not localhost.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Hello world!", "utf-8"))

def main():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()

if __name__ == '__main__':
    main()
