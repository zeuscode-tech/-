#!/usr/bin/env python3
import os
import sys
import time


def main():
    if len(sys.argv) < 3:
        print(
            "Использование: python3 runner.py N КОМАНДА [АРГУМЕНТЫ...]",
            file=sys.stderr,
        )
        return 1

    try:
        count = int(sys.argv[1])
        if count <= 0:
            raise ValueError
    except ValueError:
        print("Ошибка: N должно быть положительным целым", file=sys.stderr)
        return 1

    command = sys.argv[2:]
    children = {}
    launch_failed = False

    # Убираем буферизованный вывод перед fork.
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        for _ in range(count):
            started = time.monotonic()
            pid = os.fork()

            if pid == 0:
                try:
                    os.execvp(command[0], command)
                except OSError as error:
                    message = f"exec: {command[0]}: {error}\n"
                    os.write(2, message.encode())
                    os._exit(127 if error.errno == 2 else 126)

            children[pid] = started

    except OSError as error:
        print(f"Ошибка fork: {error}", file=sys.stderr)
        launch_failed = True

    # Даже при ошибке fork ждём уже созданных детей.
    while children:
        pid, status = os.waitpid(-1, 0)
        elapsed = time.monotonic() - children.pop(pid)
        code = os.waitstatus_to_exitcode(status)

        if code < 0:
            result = f"сигнал={-code}"
        else:
            result = f"код={code}"

        print(
            f"PID={pid} {result} время={elapsed:.3f} с",
            flush=True,
        )

    return 1 if launch_failed else 0


if __name__ == "__main__":
    sys.exit(main())
