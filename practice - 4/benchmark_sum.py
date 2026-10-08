#!/usr/bin/env python3

import multiprocessing as mp
import os
import statistics
import threading
import time

WORKERS = 4
REPEATS = 3
NUMBERS = []


def sum_range(start, end):
    total = 0
    for index in range(start, end):
        total += NUMBERS[index]
    return total


def make_ranges(length, workers):
    step = (length + workers - 1) // workers
    return [
        (start, min(start + step, length))
        for start in range(0, length, step)
    ]


def run_single(ranges):
    return sum_range(0, len(NUMBERS))


def run_threads(ranges):
    partial_sums = [0] * len(ranges)
    threads = []

    def worker(number, start, end):
        partial_sums[number] = sum_range(start, end)

    for number, (start, end) in enumerate(ranges):
        thread = threading.Thread(
            target=worker,
            args=(number, start, end),
        )
        threads.append(thread)

    # Сначала запускаем все потоки
    for thread in threads:
        thread.start()

    # Затем ожидаем все потоки
    for thread in threads:
        thread.join()

    return sum(partial_sums)


def process_worker(start, end, queue):
    queue.put(sum_range(start, end))


def run_processes(ranges):
    # Для лабораторной используем fork в Linux:
    # дочерние процессы наследуют список через copy-on-write.
    context = mp.get_context("fork")
    queue = context.Queue()
    processes = []

    for start, end in ranges:
        process = context.Process(
            target=process_worker,
            args=(start, end, queue),
        )
        processes.append(process)

    # Сначала запускаем все процессы
    for process in processes:
        process.start()

    partial_sums = [queue.get() for _ in processes]

    # Затем ожидаем их завершения
    for process in processes:
        process.join()

    return sum(partial_sums)


def measure(name, function, ranges, expected):
    times = []

    for repeat in range(1, REPEATS + 1):
        started = time.perf_counter()
        result = function(ranges)
        elapsed = time.perf_counter() - started

        if result != expected:
            raise RuntimeError(
                f"{name}: неверная сумма {result}, ожидалось {expected}"
            )

        times.append(elapsed)
        print(
            f"{name:<15} повтор {repeat}: "
            f"{elapsed:.3f} с, сумма={result}"
        )

    return times


def main():
    global NUMBERS

    print("Загрузка numbers.txt вне измерений...")
    with open("numbers.txt", encoding="utf-8") as file:
        NUMBERS = [int(line) for line in file]

    ranges = make_ranges(len(NUMBERS), WORKERS)
    expected = sum(NUMBERS)

    print(f"Логических ядер: {os.cpu_count()}")
    print(f"Чисел: {len(NUMBERS):,}")
    print(f"Повторов: {REPEATS}")
    print(f"Контрольная сумма: {expected}")
    print()

    results = {
        "Один поток": measure(
            "Один поток", run_single, ranges, expected
        ),
        "4 потока": measure(
            "4 потока", run_threads, ranges, expected
        ),
        "4 процесса": measure(
            "4 процесса", run_processes, ranges, expected
        ),
    }

    print("\nИтоговая таблица")
    print(f"{'Способ':<15} {'Запуск 1':>10} {'Запуск 2':>10} "
          f"{'Запуск 3':>10} {'Медиана':>10}")

    for name, times in results.items():
        median = statistics.median(times)
        print(
            f"{name:<15} "
            f"{times[0]:>9.3f}с "
            f"{times[1]:>9.3f}с "
            f"{times[2]:>9.3f}с "
            f"{median:>9.3f}с"
        )


if __name__ == "__main__":
    main()
