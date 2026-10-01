#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path


def get_ppid(pid):
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("PPid:"):
            return int(line.split()[1])
    raise RuntimeError("PPid не найден")


def main():
    # Первый канал передаёт PID, второй удерживает сироту живой.
    info_r, info_w = os.pipe()
    gate_r, gate_w = os.pipe()

    parent = os.fork()

    if parent == 0:
        os.close(info_r)
        os.close(gate_w)

        try:
            child = os.fork()

            if child == 0:
                os.close(info_w)
                # Ждём разрешения завершиться от наблюдателя.
                os.read(gate_r, 1)
                os.close(gate_r)
                os._exit(0)

            os.close(gate_r)
            os.write(info_w, str(child).encode())
            os.close(info_w)
            os._exit(0)
        except OSError:
            os._exit(1)

    os.close(info_w)
    os.close(gate_r)

    with os.fdopen(info_r) as pipe:
        message = pipe.read()

    _, status = os.waitpid(parent, 0)

    if not message:
        os.close(gate_w)
        raise RuntimeError("Не удалось создать ребёнка")

    child = int(message)

    try:
        adopter = get_ppid(child)
        print(f"Наблюдатель PID={os.getpid()}", flush=True)
        print(
            f"Исходный родитель PID={parent} завершился, "
            f"код={os.waitstatus_to_exitcode(status)}",
            flush=True,
        )
        print(
            f"Сирота PID={child}, новый PPID={adopter}",
            flush=True,
        )

        subprocess.run(
            [
                "ps", "-o", "pid,ppid,state,args",
                "-p", f"{child},{adopter}",
            ],
            check=True,
        )
    finally:
        # Закрытие канала даёт ребёнку EOF и разрешает выйти.
        os.close(gate_w)

    # Сироту забирает её новый родитель, а не наблюдатель.
    deadline = time.monotonic() + 10
    while Path(f"/proc/{child}").exists():
        if time.monotonic() >= deadline:
            subprocess.run(
                ["ps", "-o", "pid,ppid,state,args", "-p", str(child)]
            )
            raise RuntimeError("Новый родитель пока не убрал процесс")
        time.sleep(0.05)

    print("\nПроверка после завершения:", flush=True)
    subprocess.run(
        ["ps", "-o", "pid,ppid,state,args", "-p", f"{parent},{child}"]
    )
    print("Оба демонстрационных процесса отсутствуют.", flush=True)


if __name__ == "__main__":
    main()
