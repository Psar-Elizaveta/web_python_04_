import mimetypes
import os
import os.path
import urllib.parse
import json
import logging
import socket
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime

# from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 8080
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000

# jinja = Environment(loader=FileSystemLoader('templates'))


class Framework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        print(route.query)

        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            # case '/blog':
            #     self.render_template('blog.jinja')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    # def render_template(self, filename, status_code=200):
    #     self.send_response(status_code)
    #     self.send_header('Content-Type', 'text/html')
    #     self.end_headers()
    #
    #     with open('storage/data.json', 'r', encoding='utf-8') as file:
    #         data = json.load(file)
    #
    #     template = jinja.get_template(filename)
    #     message = None  # "Hello Sergiy!"
    #     html = template.render(blogs=data, message=message)
    #     self.wfile.write(html.encode())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


# def save_data_from_form(data):
#     parse_data = urllib.parse.unquote_plus(data.decode())
#     received_data = str(datetime.now())
#     try:
#         parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
#         parse_dict['timestamp'] = received_data
#         storage_dir = 'storage/data.json'
#         if not os.path.exists(storage_dir):
#             os.makedirs(storage_dir)
#         with open('storage/data.json', 'w', encoding='utf-8') as file:
#             json.dump(parse_dict, file, ensure_ascii=False, indent=4)
#     except ValueError as err:
#         logging.error(err)
#     except OSError as err:
#         logging.error(err)


def save_data_from_form(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        new_data = {current_time: {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}}

        file_path = "storage/data.json"

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = {}

        existing_data.update(new_data)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=2)

    except ValueError as error:
        logging.error(f"ValueError: {error}")
    except OSError as oser:
        logging.error(f"OSError: {oser}")


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, Framework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
