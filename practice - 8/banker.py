#!/usr/bin/env python3

import sys
from pathlib import Path


class Banker:
    def __init__(self, available, allocation, maximum, order):
        self.available = available
        self.allocation = allocation
        self.maximum = maximum
        self.order = order
        self.resource_count = len(available)

    def need(self, pid):
        return [
            self.maximum[pid][index] - self.allocation[pid][index]
            for index in range(self.resource_count)
        ]

    def safety_check(self):
        work = self.available.copy()
        finished = {pid: False for pid in self.order}
        sequence = []

        while len(sequence) < len(self.order):
            progress = False

            for pid in self.order:
                if finished[pid]:
                    continue

                required = self.need(pid)

                if all(
                    required[index] <= work[index]
                    for index in range(self.resource_count)
                ):
                    for index in range(self.resource_count):
                        work[index] += self.allocation[pid][index]

                    finished[pid] = True
                    sequence.append(pid)
                    progress = True

            if not progress:
                break

        safe = len(sequence) == len(self.order)
        blocked = [
            pid for pid in self.order
            if not finished[pid]
        ]

        return safe, sequence, blocked

    def request(self, pid, vector):
        if pid not in self.allocation:
            return False, f"Процесс {pid} не найден"

        if len(vector) != self.resource_count:
            return False, (
                f"Ожидалось {self.resource_count} значений ресурсов"
            )

        if any(value < 0 for value in vector):
            return False, "Запрос не может содержать отрицательные значения"

        required = self.need(pid)

        if any(
            vector[index] > required[index]
            for index in range(self.resource_count)
        ):
            return False, (
                f"Запрос превышает оставшуюся потребность {required}"
            )

        if any(
            vector[index] > self.available[index]
            for index in range(self.resource_count)
        ):
            return False, (
                f"Недостаточно доступных ресурсов: {self.available}"
            )

        old_available = self.available.copy()
        old_allocation = self.allocation[pid].copy()

        for index in range(self.resource_count):
            self.available[index] -= vector[index]
            self.allocation[pid][index] += vector[index]

        safe, sequence, blocked = self.safety_check()

        if not safe:
            self.available = old_available
            self.allocation[pid] = old_allocation

            return False, (
                "Запрос привёл бы к небезопасному состоянию. "
                f"Откат выполнен. Заблокированы: {', '.join(blocked)}"
            )

        return True, (
            "Запрос разрешён. Безопасная последовательность: "
            + " -> ".join(sequence)
        )

    def show(self):
        print(f"Available: {self.available}")
        print()
        print(
            f"{'PID':<6}"
            f"{'Allocation':<20}"
            f"{'Max':<20}"
            f"{'Need':<20}"
        )

        for pid in self.order:
            print(
                f"{pid:<6}"
                f"{str(self.allocation[pid]):<20}"
                f"{str(self.maximum[pid]):<20}"
                f"{str(self.need(pid)):<20}"
            )


def load_bank(path):
    available = None
    allocation = {}
    maximum = {}
    order = []
    section = None

    for raw_line in Path(path).read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("Available:"):
            available = [
                int(value)
                for value in line.split(":", 1)[1].split()
            ]
            continue

        if line == "Allocation:":
            section = "allocation"
            continue

        if line == "Max:":
            section = "maximum"
            continue

        parts = line.split()
        pid = parts[0]
        values = [int(value) for value in parts[1:]]

        if section == "allocation":
            allocation[pid] = values
            order.append(pid)
        elif section == "maximum":
            maximum[pid] = values
        else:
            raise ValueError(f"Строка вне секции: {line}")

    if available is None:
        raise ValueError("Не задан вектор Available")

    if set(allocation) != set(maximum):
        raise ValueError("Списки процессов Allocation и Max различаются")

    resource_count = len(available)

    for pid in order:
        if (
            len(allocation[pid]) != resource_count
            or len(maximum[pid]) != resource_count
        ):
            raise ValueError(
                f"Неверное количество ресурсов у {pid}"
            )

        if any(
            allocation[pid][index] > maximum[pid][index]
            for index in range(resource_count)
        ):
            raise ValueError(
                f"Allocation превышает Max у {pid}"
            )

    return Banker(
        available,
        allocation,
        maximum,
        order,
    )


def print_safety_result(banker):
    safe, sequence, blocked = banker.safety_check()

    if safe:
        print("Состояние безопасное: True")
        print(
            "Безопасная последовательность: "
            + " -> ".join(sequence)
        )
    else:
        print("Состояние безопасное: False")
        print(
            "Безопасная последовательность не существует"
        )
        print(
            "Не могут завершиться: "
            + ", ".join(blocked)
        )


def main():
    if len(sys.argv) != 2:
        print(f"Использование: {sys.argv[0]} bank.txt")
        raise SystemExit(1)

    banker = load_bank(sys.argv[1])

    print(f"Загружен файл: {sys.argv[1]}")
    banker.show()
    print()
    print_safety_result(banker)

    print()
    print("Команды:")
    print("  safe")
    print("  show")
    print("  request PID R1 R2 R3")
    print("  quit")

    while True:
        try:
            command = input("banker> ").strip()
        except EOFError:
            print()
            break

        if not command:
            continue

        parts = command.split()
        action = parts[0].lower()

        if action in {"quit", "exit"}:
            break

        if action == "safe":
            print_safety_result(banker)
            continue

        if action == "show":
            banker.show()
            continue

        if action == "request":
            if len(parts) != banker.resource_count + 2:
                print(
                    "Ошибка: request PID "
                    + " ".join(
                        f"R{index + 1}"
                        for index in range(
                            banker.resource_count
                        )
                    )
                )
                continue

            pid = parts[1]

            try:
                vector = [
                    int(value)
                    for value in parts[2:]
                ]
            except ValueError:
                print("Ошибка: ресурсы должны быть целыми числами")
                continue

            accepted, message = banker.request(pid, vector)
            print(f"Запрос принят: {accepted}")
            print(message)
            continue

        print(f"Неизвестная команда: {action}")


if __name__ == "__main__":
    main()
