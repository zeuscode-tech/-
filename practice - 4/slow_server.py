#!/usr/bin/env python3

import os
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8000
DELAY = 0.15


class SlowHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        time.sleep(DELAY)
        super().do_GET()

    def log_message(self, format, *args):
        pass


def main():
    os.chdir("web")
    server = ThreadingHTTPServer((HOST, PORT), SlowHandler)

    print(f"Сервер запущен: http://{HOST}:{PORT}")
    print(f"Задержка каждого запроса: {DELAY} с")
    print("Для остановки нажмите Ctrl+C")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
