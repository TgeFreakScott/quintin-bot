
from quintin_bot import bot  # This makes sure the bot starts
from http.server import BaseHTTPRequestHandler
from io import BytesIO

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write(b"Quintin is alive and brewing stew.")
