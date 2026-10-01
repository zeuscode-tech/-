#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path


def main():
    pid = os.fork()

    if pid == 0:
        os._exit(42)

    print(f"Родитель PID={os.getpid()}, ребёнок PID={pid}", flush=True)

    try:
        # Ждём состояния Z, пока не забирая код завершения.
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = Path(f"/proc/{pid}/status").read_text()
            if any(
                line.startswith("State:") and line.split()[1] == "Z"
                for line in status.splitlines()
            ):
                break
            time.sleep(0.01)
        else:
            raise RuntimeError("Не удалось дождаться состояния Z")

        print("\nДо waitpid: ребёнок — зомби", flush=True)
        subprocess.run(
            ["ps", "-o", "pid,ppid,state,stat,comm", "-p", str(pid)],
            check=True,
        )
    finally:
        # Обязательно забираем результат завершившегося ребёнка.
        waited_pid, status = os.waitpid(pid, 0)
        code = os.waitstatus_to_exitcode(status)
        print(f"\nwaitpid: PID={waited_pid}, код={code}", flush=True)

    print("\nПосле waitpid:", flush=True)
    result = subprocess.run(
        ["ps", "-o", "pid,ppid,state,stat,comm", "-p", str(pid)]
    )

    if result.returncode == 1:
        print("Процесс отсутствует: зомби убран.", flush=True)
    elif result.returncode != 0:
        raise RuntimeError("Ошибка проверки ps")


if __name__ == "__main__":
    main()
