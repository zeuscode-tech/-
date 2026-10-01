#!/usr/bin/env python3
import os
from pathlib import Path


def read_process(path, uid):
    try:
        fields = {}
        for line in (path / "status").read_text().splitlines():
            key, _, value = line.partition(":")
            fields[key] = value.strip()

        if int(fields["Uid"].split()[0]) != uid:
            return None

        return {
            "pid": int(fields["Pid"]),
            "ppid": int(fields["PPid"]),
            "name": fields["Name"],
            "state": fields["State"].split()[0],
            "rss": int(fields.get("VmRSS", "0 kB").split()[0]),
        }
    except (OSError, KeyError, ValueError):
        # Процесс мог завершиться или стать недоступным.
        return None


def main():
    uid = os.getuid()
    processes = {}

    for path in Path("/proc").iterdir():
        if path.name.isdigit():
            process = read_process(path, uid)
            if process is not None:
                processes[process["pid"]] = process

    children = {}
    roots = []

    for pid, process in processes.items():
        parent = process["ppid"]
        if parent in processes:
            children.setdefault(parent, []).append(pid)
        else:
            roots.append(pid)

    print(f"Процессы пользователя UID={uid}")
    print("PID      STATE RSS(KiB)  NAME")

    visited = set()

    def show_tree(root):
        stack = [(root, 0)]
        while stack:
            pid, depth = stack.pop()
            if pid in visited:
                continue
            visited.add(pid)

            process = processes[pid]
            indent = "  " * depth
            print(
                f"{indent}{pid:<8} {process['state']:<5} "
                f"{process['rss']:<9} {process['name']}"
            )

            for child in sorted(children.get(pid, []), reverse=True):
                stack.append((child, depth + 1))

    for root in sorted(roots):
        show_tree(root)

    # /proc меняется во время чтения: показываем также
    # процессы, которые не удалось привязать к дереву.
    for pid in sorted(processes):
        if pid not in visited:
            show_tree(pid)


if __name__ == "__main__":
    main()
