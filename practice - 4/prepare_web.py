#!/usr/bin/env python3

from pathlib import Path

directory = Path("web")
directory.mkdir(exist_ok=True)

content = ("Практическая работа по потокам\n" * 4000).encode("utf-8")

for number in range(1, 21):
    path = directory / f"file{number:02d}.txt"
    path.write_bytes(content)

print("Создано 20 файлов")
