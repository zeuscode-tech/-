#!/usr/bin/env python3

import argparse
from collections import deque


def read_processes(filename):
    processes = []

    with open(filename, encoding="utf-8") as file:
        for order, line in enumerate(file):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) != 4:
                raise ValueError(
                    f"Неверная строка: {line!r}. "
                    "Ожидается: PID arrival burst priority"
                )

            pid, arrival, burst, priority = parts

            processes.append({
                "pid": pid,
                "arrival": int(arrival),
                "burst": int(burst),
                "priority": int(priority),
                "order": order,
            })

    if not processes:
        raise ValueError("Файл не содержит процессов")

    return processes


def add_interval(intervals, pid, start, end):
    if start == end:
        return

    # Объединяем соседние интервалы одного процесса.
    if intervals and intervals[-1][0] == pid:
        old_pid, old_start, old_end = intervals[-1]

        if old_end == start:
            intervals[-1] = (old_pid, old_start, end)
            return

    intervals.append((pid, start, end))


def simulate_fcfs(processes):
    intervals = []
    completed = set()
    time = 0

    while len(completed) < len(processes):
        ready = [
            process
            for process in processes
            if process["pid"] not in completed
            and process["arrival"] <= time
        ]

        if not ready:
            next_time = min(
                process["arrival"]
                for process in processes
                if process["pid"] not in completed
            )
            add_interval(intervals, "IDLE", time, next_time)
            time = next_time
            continue

        current = min(
            ready,
            key=lambda process: (
                process["arrival"],
                process["order"],
            ),
        )

        start = time
        time += current["burst"]

        add_interval(
            intervals,
            current["pid"],
            start,
            time,
        )
        completed.add(current["pid"])

    return intervals


def simulate_sjf(processes):
    intervals = []
    completed = set()
    time = 0

    while len(completed) < len(processes):
        ready = [
            process
            for process in processes
            if process["pid"] not in completed
            and process["arrival"] <= time
        ]

        if not ready:
            next_time = min(
                process["arrival"]
                for process in processes
                if process["pid"] not in completed
            )
            add_interval(intervals, "IDLE", time, next_time)
            time = next_time
            continue

        current = min(
            ready,
            key=lambda process: (
                process["burst"],
                process["arrival"],
                process["order"],
            ),
        )

        start = time
        time += current["burst"]

        add_interval(
            intervals,
            current["pid"],
            start,
            time,
        )
        completed.add(current["pid"])

    return intervals


def simulate_srtf(processes):
    intervals = []
    remaining = {
        process["pid"]: process["burst"]
        for process in processes
    }
    time = 0

    while any(value > 0 for value in remaining.values()):
        ready = [
            process
            for process in processes
            if process["arrival"] <= time
            and remaining[process["pid"]] > 0
        ]

        if not ready:
            next_time = min(
                process["arrival"]
                for process in processes
                if remaining[process["pid"]] > 0
                and process["arrival"] > time
            )
            add_interval(intervals, "IDLE", time, next_time)
            time = next_time
            continue

        current = min(
            ready,
            key=lambda process: (
                remaining[process["pid"]],
                process["arrival"],
                process["order"],
            ),
        )

        add_interval(
            intervals,
            current["pid"],
            time,
            time + 1,
        )

        remaining[current["pid"]] -= 1
        time += 1

    return intervals


def simulate_priority(processes, aging=0):
    intervals = []
    remaining = {
        process["pid"]: process["burst"]
        for process in processes
    }
    time = 0

    def effective_priority(process):
        executed = (
            process["burst"]
            - remaining[process["pid"]]
        )
        waiting = (
            time
            - process["arrival"]
            - executed
        )

        if aging > 0:
            return max(
                0,
                process["priority"] - waiting // aging,
            )

        return process["priority"]

    while any(value > 0 for value in remaining.values()):
        ready = [
            process
            for process in processes
            if process["arrival"] <= time
            and remaining[process["pid"]] > 0
        ]

        if not ready:
            next_time = min(
                process["arrival"]
                for process in processes
                if remaining[process["pid"]] > 0
                and process["arrival"] > time
            )
            add_interval(intervals, "IDLE", time, next_time)
            time = next_time
            continue

        current = min(
            ready,
            key=lambda process: (
                effective_priority(process),
                process["arrival"],
                process["order"],
            ),
        )

        add_interval(
            intervals,
            current["pid"],
            time,
            time + 1,
        )

        remaining[current["pid"]] -= 1
        time += 1

    return intervals


def simulate_rr(processes, quantum):
    if quantum <= 0:
        raise ValueError("Квант должен быть больше нуля")

    intervals = []
    remaining = {
        process["pid"]: process["burst"]
        for process in processes
    }

    ordered = sorted(
        processes,
        key=lambda process: (
            process["arrival"],
            process["order"],
        ),
    )

    queue = deque()
    next_process = 0
    time = 0

    while (
        next_process < len(ordered)
        or queue
        or any(value > 0 for value in remaining.values())
    ):
        while (
            next_process < len(ordered)
            and ordered[next_process]["arrival"] <= time
        ):
            queue.append(ordered[next_process])
            next_process += 1

        if not queue:
            if next_process >= len(ordered):
                break

            next_time = ordered[next_process]["arrival"]
            add_interval(intervals, "IDLE", time, next_time)
            time = next_time
            continue

        current = queue.popleft()
        pid = current["pid"]
        start = time
        duration = min(quantum, remaining[pid])
        end = time + duration

        add_interval(intervals, pid, start, end)
        remaining[pid] -= duration
        time = end

        # Процессы, прибывшие во время кванта,
        # добавляются в очередь.
        while (
            next_process < len(ordered)
            and ordered[next_process]["arrival"] < time
        ):
            queue.append(ordered[next_process])
            next_process += 1

        # Для совпадения с контрольным эталоном
        # вытесненный процесс возвращается в очередь.
        if remaining[pid] > 0:
            queue.append(current)

        # Затем учитываются процессы, прибывшие
        # точно в момент окончания кванта.
        while (
            next_process < len(ordered)
            and ordered[next_process]["arrival"] == time
        ):
            queue.append(ordered[next_process])
            next_process += 1

    return intervals


def simulate(processes, algorithm, **params):
    algorithm = algorithm.lower()

    if algorithm == "fcfs":
        return simulate_fcfs(processes)

    if algorithm == "sjf":
        return simulate_sjf(processes)

    if algorithm == "srtf":
        return simulate_srtf(processes)

    if algorithm == "priority":
        return simulate_priority(
            processes,
            aging=params.get("aging", 0),
        )

    if algorithm == "rr":
        return simulate_rr(
            processes,
            quantum=params.get("quantum", 3),
        )

    raise ValueError(f"Неизвестный алгоритм: {algorithm}")


def calculate_metrics(processes, intervals):
    completion = {}
    first_start = {}

    for pid, start, end in intervals:
        if pid == "IDLE":
            continue

        if pid not in first_start:
            first_start[pid] = start

        completion[pid] = end

    rows = []

    for process in processes:
        pid = process["pid"]
        turnaround = completion[pid] - process["arrival"]
        waiting = turnaround - process["burst"]
        response = first_start[pid] - process["arrival"]

        rows.append({
            "pid": pid,
            "waiting": waiting,
            "turnaround": turnaround,
            "response": response,
        })

    count = len(rows)
    busy_time = sum(process["burst"] for process in processes)
    finish_time = max(end for _, _, end in intervals)
    cpu_usage = 100 * busy_time / finish_time

    switches = 0
    previous = None

    for pid, _, _ in intervals:
        if pid == "IDLE":
            previous = None
            continue

        if previous is not None and pid != previous:
            switches += 1

        previous = pid

    summary = {
        "avg_waiting": sum(
            row["waiting"] for row in rows
        ) / count,
        "avg_turnaround": sum(
            row["turnaround"] for row in rows
        ) / count,
        "avg_response": sum(
            row["response"] for row in rows
        ) / count,
        "cpu_usage": cpu_usage,
        "switches": switches,
    }

    return rows, summary


def print_result(processes, intervals):
    rows, summary = calculate_metrics(
        processes,
        intervals,
    )

    print("\nДиаграмма выполнения:")
    print(
        " | ".join(
            f"{pid}[{start}-{end}]"
            for pid, start, end in intervals
        )
    )

    print("\nМетрики процессов:")
    print(
        f"{'PID':<8}"
        f"{'Ожидание':>12}"
        f"{'Оборот':>12}"
        f"{'Отклик':>12}"
    )

    for row in rows:
        print(
            f"{row['pid']:<8}"
            f"{row['waiting']:>12}"
            f"{row['turnaround']:>12}"
            f"{row['response']:>12}"
        )

    print("\nСредние значения:")
    print(
        f"Среднее ожидание: "
        f"{summary['avg_waiting']:.2f}"
    )
    print(
        f"Средний оборот: "
        f"{summary['avg_turnaround']:.2f}"
    )
    print(
        f"Средний отклик: "
        f"{summary['avg_response']:.2f}"
    )
    print(
        f"Загрузка CPU: "
        f"{summary['cpu_usage']:.2f}%"
    )
    print(
        f"Переключения: "
        f"{summary['switches']}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Симулятор планирования CPU"
    )

    parser.add_argument(
        "filename",
        help="Файл процессов",
    )
    parser.add_argument(
        "--algo",
        required=True,
        choices=[
            "fcfs",
            "sjf",
            "srtf",
            "priority",
            "rr",
        ],
        help="Алгоритм планирования",
    )
    parser.add_argument(
        "--quantum",
        type=int,
        default=3,
        help="Квант для Round Robin",
    )
    parser.add_argument(
        "--aging",
        type=int,
        default=0,
        help=(
            "Через сколько единиц ожидания "
            "повышать приоритет"
        ),
    )

    args = parser.parse_args()
    processes = read_processes(args.filename)

    intervals = simulate(
        processes,
        args.algo,
        quantum=args.quantum,
        aging=args.aging,
    )

    print(f"Алгоритм: {args.algo.upper()}")

    if args.algo == "rr":
        print(f"Квант: {args.quantum}")

    if args.algo == "priority":
        print(f"Старение: {args.aging}")

    print_result(processes, intervals)


if __name__ == "__main__":
    main()

