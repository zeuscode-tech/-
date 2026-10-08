#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

FIFO_DIRECTORY = Path("/tmp/lab7_ipc_zeus")
REQUEST_FIFO = FIFO_DIRECTORY / "request.fifo"
RESPONSE_FIFO = FIFO_DIRECTORY / "response.fifo"


def main():
    parser = argparse.ArgumentParser(
        description="Клиент FIFO-калькулятора"
    )
    parser.add_argument(
        "expression",
        nargs="+",
        help=(
            "Арифметическое выражение "
            "или quit"
        ),
    )

    args = parser.parse_args()
    expression = " ".join(args.expression)

    if not REQUEST_FIFO.exists():
        print(
            "Ошибка: FIFO-сервер не запущен",
            file=sys.stderr,
        )
        return 1

    # Сначала отправляем запрос.
    with REQUEST_FIFO.open(
        "w",
        encoding="utf-8",
    ) as request:
        request.write(expression + "\n")
        request.flush()

    # Затем читаем ответ из второго FIFO.
    with RESPONSE_FIFO.open(
        "r",
        encoding="utf-8",
    ) as response:
        answer = response.readline().strip()

    print("Ответ сервера:", answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
