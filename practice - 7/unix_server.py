#!/usr/bin/env python3

import multiprocessing as mp
import os
import signal
import socket
from pathlib import Path

from fifo_server import safe_calculate

SOCKET_PATH = Path("/tmp/lab7_ipc_zeus.sock")


def handle_client(connection, stop_event):
    """Обрабатывает одного клиента в отдельном процессе."""
    try:
        request = connection.recv(4096).decode("utf-8").strip()

        if request == "quit":
            response = "Сервер завершает работу"
            stop_event.set()
        else:
            try:
                result = safe_calculate(request)
                response = f"{request} = {result}"
            except Exception as error:
                response = f"Ошибка: {type(error).__name__}: {error}"

        connection.sendall(response.encode("utf-8"))

        print(
            f"Процесс {os.getpid()}: запрос={request!r}, ответ={response!r}",
            flush=True,
        )
    finally:
        connection.close()


def cleanup():
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()


def main():
    cleanup()

    stop_event = mp.Event()
    children = []

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(SOCKET_PATH))
    server.listen()
    server.settimeout(0.5)

    def request_stop(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    print(f"Unix-сервер запущен: {SOCKET_PATH}", flush=True)
    print("Каждый клиент обслуживается отдельным процессом", flush=True)

    try:
        while not stop_event.is_set():
            try:
                connection, _ = server.accept()
            except socket.timeout:
                continue

            process = mp.Process(
                target=handle_client,
                args=(connection, stop_event),
            )
            process.start()
            connection.close()
            children.append(process)

            active = []
            for child in children:
                if child.is_alive():
                    active.append(child)
                else:
                    child.join()
            children = active
    finally:
        server.close()

        for child in children:
            child.join()

        cleanup()
        print("Unix-сервер завершён, файл сокета удалён", flush=True)


if __name__ == "__main__":
    main()
