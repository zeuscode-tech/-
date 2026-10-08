#!/usr/bin/env python3

from pathlib import Path
import random
import time

COUNT = 10_000_000
OUTPUT = Path("numbers.txt")
SEED = 42


def main():
    random.seed(SEED)
    started = time.perf_counter()

    with OUTPUT.open("w", encoding="utf-8") as file:
        for _ in range(COUNT):
            file.write(f"{random.randint(1, 100)}\n")

    elapsed = time.perf_counter() - started

    print(f"Создан файл: {OUTPUT}")
    print(f"Количество чисел: {COUNT:,}")
    print(f"Размер: {OUTPUT.stat().st_size / 1024 / 1024:.1f} МБ")
    print(f"Время генерации: {elapsed:.2f} с")


if __name__ == "__main__":
    main()

