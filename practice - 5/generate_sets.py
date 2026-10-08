#!/usr/bin/env python3

from pathlib import Path


SET2_BURSTS = [
    18, 14, 20, 11, 16,
    13, 19, 12, 17, 15,
    20, 10, 18, 14, 16,
    12, 19, 13, 17, 15,
]

SET3_BURSTS = [
    60, 2, 1, 3, 2,
    1, 4, 2, 1, 3,
    2, 1, 4, 2, 1,
    3, 2, 1, 4, 2,
]


def write_set(path, bursts):
    rows = []

    for index, burst in enumerate(bursts, start=1):
        pid = f"P{index}"
        arrival = index - 1
        priority = ((index - 1) % 5) + 1
        rows.append(f"{pid} {arrival} {burst} {priority}")

    Path(path).write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_starvation_set():
    rows = ["LOW 0 10 20"]

    # Каждый момент появляется новый короткий процесс
    # с высоким приоритетом.
    for index in range(50):
        rows.append(f"H{index + 1:02d} {index} 1 1")

    Path("starvation.txt").write_text(
        "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def main():
    write_set("set2.txt", SET2_BURSTS)
    write_set("set3.txt", SET3_BURSTS)
    write_starvation_set()

    print("Созданы:")
    print("- set2.txt: 20 CPU-bound процессов")
    print("- set3.txt: один длинный и 19 коротких процессов")
    print("- starvation.txt: набор для демонстрации старения")


if __name__ == "__main__":
    main()
