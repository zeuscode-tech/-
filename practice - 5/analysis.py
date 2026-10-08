#!/usr/bin/env python3

import csv

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from sched import (
    read_processes,
    simulate,
    calculate_metrics,
)


ALGORITHMS = [
    ("FCFS", "fcfs", {}),
    ("SJF", "sjf", {}),
    ("SRTF", "srtf", {}),
    ("Priority", "priority", {"aging": 0}),
    ("RR q=3", "rr", {"quantum": 3}),
]


def compare_algorithms(filename):
    processes = read_processes(filename)
    rows = []

    for title, algorithm, params in ALGORITHMS:
        intervals = simulate(
            processes,
            algorithm,
            **params,
        )
        _, metrics = calculate_metrics(
            processes,
            intervals,
        )

        rows.append({
            "algorithm": title,
            **metrics,
        })

    print(f"\nНабор: {filename}")
    print(
        f"{'Алгоритм':<12}"
        f"{'Ожидание':>12}"
        f"{'Оборот':>12}"
        f"{'Отклик':>12}"
        f"{'CPU, %':>10}"
        f"{'Перекл.':>10}"
    )

    for row in rows:
        print(
            f"{row['algorithm']:<12}"
            f"{row['avg_waiting']:>12.2f}"
            f"{row['avg_turnaround']:>12.2f}"
            f"{row['avg_response']:>12.2f}"
            f"{row['cpu_usage']:>10.2f}"
            f"{row['switches']:>10}"
        )

    return rows


def analyze_rr():
    processes = read_processes("set2.txt")
    results = []

    for quantum in range(1, 11):
        intervals = simulate(
            processes,
            "rr",
            quantum=quantum,
        )
        _, metrics = calculate_metrics(
            processes,
            intervals,
        )

        results.append({
            "quantum": quantum,
            "waiting": metrics["avg_waiting"],
            "switches": metrics["switches"],
        })

    print("\nRound Robin на set2")
    print(
        f"{'Квант':>7}"
        f"{'Среднее ожидание':>20}"
        f"{'Переключения':>17}"
    )

    for row in results:
        print(
            f"{row['quantum']:>7}"
            f"{row['waiting']:>20.2f}"
            f"{row['switches']:>17}"
        )

    with open(
        "rr_quantum.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "quantum",
                "waiting",
                "switches",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    quantums = [
        row["quantum"]
        for row in results
    ]
    waiting = [
        row["waiting"]
        for row in results
    ]
    switches = [
        row["switches"]
        for row in results
    ]

    figure, first_axis = plt.subplots(
        figsize=(10, 6)
    )
    second_axis = first_axis.twinx()

    first_axis.plot(
        quantums,
        waiting,
        marker="o",
        color="tab:blue",
        label="Среднее ожидание",
    )
    second_axis.plot(
        quantums,
        switches,
        marker="s",
        color="tab:red",
        label="Переключения",
    )

    first_axis.set_xlabel("Квант Round Robin")
    first_axis.set_ylabel(
        "Среднее время ожидания",
        color="tab:blue",
    )
    second_axis.set_ylabel(
        "Число переключений",
        color="tab:red",
    )

    first_axis.set_xticks(quantums)
    first_axis.grid(True, alpha=0.3)
    plt.title(
        "Влияние кванта RR на ожидание "
        "и число переключений"
    )
    figure.tight_layout()
    figure.savefig(
        "rr_quantum.png",
        dpi=160,
    )

    print("\nСозданы rr_quantum.csv и rr_quantum.png")


def first_start(intervals, pid):
    return min(
        start
        for current_pid, start, _ in intervals
        if current_pid == pid
    )


def demonstrate_aging():
    processes = read_processes("starvation.txt")

    without_aging = simulate(
        processes,
        "priority",
        aging=0,
    )
    with_aging = simulate(
        processes,
        "priority",
        aging=2,
    )

    without_start = first_start(
        without_aging,
        "LOW",
    )
    with_start = first_start(
        with_aging,
        "LOW",
    )

    _, without_metrics = calculate_metrics(
        processes,
        without_aging,
    )
    _, with_metrics = calculate_metrics(
        processes,
        with_aging,
    )

    print("\nДемонстрация старения")
    print(
        "LOW без старения впервые запущен:",
        without_start,
    )
    print(
        "LOW со старением впервые запущен:",
        with_start,
    )
    print(
        "Среднее ожидание без старения:",
        f"{without_metrics['avg_waiting']:.2f}",
    )
    print(
        "Среднее ожидание со старением:",
        f"{with_metrics['avg_waiting']:.2f}",
    )

    print(
        "\nБез старения LOW ждёт завершения "
        "потока высокоприоритетных процессов."
    )
    print(
        "При aging=2 его эффективный приоритет "
        "повышается каждые две единицы ожидания."
    )


def main():
    for filename in [
        "set1.txt",
        "set2.txt",
        "set3.txt",
    ]:
        compare_algorithms(filename)

    analyze_rr()
    demonstrate_aging()


if __name__ == "__main__":
    main()
