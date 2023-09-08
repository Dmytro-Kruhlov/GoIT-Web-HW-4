import json
import logging
import pathlib
import socket
import urllib.parse
import mimetypes
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

BASE_DIR = pathlib.Path()
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    print(f"Send data {body}")
    client_socket.close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())

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


class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        send_data_to_socket(body)
        self.send_response(302)
        self.send_header("Location", "index.html")
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)

        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message.html":
                self.send_html("message.html")
            case _:
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
    address = ("0.0.0.0", 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def run_socket_server(ip, port):
    logging.info(f"Server start")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)

    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            print(f"Receive data {data}")
            save_data(data)

    except KeyboardInterrupt:
        logging.info("Socket server stopped")
    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket_server = Thread(run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket_server.start()
