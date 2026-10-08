#!/usr/bin/env python3

import sys
from collections import defaultdict
from pathlib import Path


class WaitGraphDetector:
    def __init__(self):
        self.owners = {}
        self.waiting = {}
        self.processes = set()
        self.violations = []

    def acquire(self, pid, resource):
        self.processes.add(pid)

        owner = self.owners.get(resource)

        if owner is not None and owner != pid:
            self.violations.append(
                f"{pid} пытается захватить занятый {resource}; "
                f"владелец {owner}"
            )
            self.waiting[pid] = resource
            return

        self.owners[resource] = pid
        self.waiting.pop(pid, None)

    def release(self, pid, resource):
        self.processes.add(pid)
        owner = self.owners.get(resource)

        if owner is None:
            self.violations.append(
                f"{pid} пытается освободить свободный {resource}"
            )
            return

        if owner != pid:
            self.violations.append(
                f"{pid} пытается освободить {resource}, "
                f"которым владеет {owner}"
            )
            return

        del self.owners[resource]

    def wait(self, pid, resource):
        self.processes.add(pid)
        self.waiting[pid] = resource

    def build_graph(self):
        graph = defaultdict(set)

        for pid in self.processes:
            graph[pid]

        for waiting_pid, resource in self.waiting.items():
            owner = self.owners.get(resource)

            if owner is not None and owner != waiting_pid:
                graph[waiting_pid].add(owner)

        return graph

    def find_cycle(self):
        graph = self.build_graph()
        color = {
            pid: 0
            for pid in graph
        }
        stack = []
        positions = {}

        def dfs(pid):
            color[pid] = 1
            positions[pid] = len(stack)
            stack.append(pid)

            for neighbour in sorted(graph[pid]):
                if color[neighbour] == 0:
                    cycle = dfs(neighbour)

                    if cycle is not None:
                        return cycle

                elif color[neighbour] == 1:
                    start = positions[neighbour]
                    return stack[start:] + [neighbour]

            stack.pop()
            positions.pop(pid, None)
            color[pid] = 2
            return None

        for pid in sorted(graph):
            if color[pid] == 0:
                cycle = dfs(pid)

                if cycle is not None:
                    return cycle

        return None

    def show_graph(self):
        graph = self.build_graph()
        edges = []

        for source in sorted(graph):
            for target in sorted(graph[source]):
                edges.append((source, target))

        if not edges:
            print("Граф ожидания: рёбер нет")
            return

        print("Граф ожидания:")

        for source, target in edges:
            resource = self.waiting[source]
            print(
                f"  {source} -> {target} "
                f"(ожидает {resource})"
            )


def process_journal(path):
    detector = WaitGraphDetector()

    lines = Path(path).read_text(
        encoding="utf-8"
    ).splitlines()

    print(f"Журнал: {path}")
    print()

    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split()

        if len(parts) != 3:
            raise ValueError(
                f"Строка {line_number}: ожидалось "
                "ДЕЙСТВИЕ PID РЕСУРС"
            )

        action, pid, resource = parts

        print(
            f"{line_number}: "
            f"{action} {pid} {resource}"
        )

        if action == "acquire":
            detector.acquire(pid, resource)
        elif action == "release":
            detector.release(pid, resource)
        elif action == "wait":
            detector.wait(pid, resource)
        else:
            raise ValueError(
                f"Строка {line_number}: "
                f"неизвестное действие {action}"
            )

        graph = detector.build_graph()

        for source in sorted(graph):
            for target in sorted(graph[source]):
                print(f"    ребро: {source} -> {target}")

        cycle = detector.find_cycle()

        if cycle is not None:
            participants = list(dict.fromkeys(cycle[:-1]))

            print()
            print("Взаимоблокировка обнаружена: True")
            print("Цикл: " + " -> ".join(cycle))
            print(
                "Участники: "
                + ", ".join(participants)
            )

            if detector.violations:
                print("Нарушения журнала:")

                for message in detector.violations:
                    print(f"  - {message}")

            return True

    print()
    detector.show_graph()
    print("Взаимоблокировка обнаружена: False")

    if detector.violations:
        print("Нарушения журнала:")

        for message in detector.violations:
            print(f"  - {message}")
    else:
        print("Нарушений журнала: 0")

    return False


def main():
    if len(sys.argv) != 2:
        print(
            f"Использование: {sys.argv[0]} events.txt"
        )
        raise SystemExit(1)

    process_journal(sys.argv[1])


if __name__ == "__main__":
    main()
