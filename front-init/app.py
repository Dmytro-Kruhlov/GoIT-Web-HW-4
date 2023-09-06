import json
import pathlib
import urllib.parse
import mimetypes
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = pathlib.Path()


class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # self.send_html("message.html")
        body = self.rfile.read(int(self.headers["Content-Length"]))
        body = urllib.parse.unquote_plus(body.decode())
        self.write_data(body)
        self.send_response(302)
        self.send_header("Location", "index.html")
        self.end_headers()

    def write_data(self, body):
        value = {kay: value for kay, value in [el.split("=") for el in body.split("&")]}
        payload = {str(datetime.now()): value}
        try:
            with open(BASE_DIR.joinpath("storage/data.json"), "r", encoding="utf-8") as fd:
                old_data = json.load(fd)
        except FileNotFoundError:
            old_data = {}
        payload.update(old_data)
        with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as fd:
            json.dump(payload, fd, ensure_ascii=False, indent=2)

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)

        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message.html":
                self.send_html("message.html")
            case _:
                print(type(BASE_DIR))
                print(route.path)
                print(type(route.path))
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type)
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = ("", 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == "__main__":
    run()
