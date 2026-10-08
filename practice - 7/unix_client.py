#!/usr/bin/env python3

import socket
import sys
from pathlib import Path

SOCKET_PATH = Path("/tmp/lab7_ipc_zeus.sock")


def main():
    if len(sys.argv) < 2:
        print(f"Использование: {sys.argv[0]} ВЫРАЖЕНИЕ")
        raise SystemExit(1)

    expression = " ".join(sys.argv[1:])

    if not SOCKET_PATH.exists():
        print("Ошибка: сервер не запущен")
        raise SystemExit(1)

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        client.connect(str(SOCKET_PATH))
        client.sendall(expression.encode("utf-8"))
        client.shutdown(socket.SHUT_WR)

        parts = []
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            parts.append(chunk)

        response = b"".join(parts).decode("utf-8")
        print(f"Ответ сервера: {response}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
