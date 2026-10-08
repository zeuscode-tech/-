#!/usr/bin/env python3

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from urllib.request import urlopen

WORKERS = 4
REPEATS = 3

URLS = [
    f"http://127.0.0.1:8000/file{number:02d}.txt"
    for number in range(1, 21)
]


def download(url):
    with urlopen(url, timeout=10) as response:
        return len(response.read())


def sequential():
    return sum(download(url) for url in URLS)


def with_threads():
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        return sum(executor.map(download, URLS))


def with_processes():
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        return sum(executor.map(download, URLS))


def measure(name, function, expected=None):
    times = []
    result = None

    for repeat in range(1, REPEATS + 1):
        started = time.perf_counter()
        result = function()
        elapsed = time.perf_counter() - started

        if expected is not None and result != expected:
            raise RuntimeError(
                f"{name}: загружено {result} байт, ожидалось {expected}"
            )

        times.append(elapsed)
        print(
            f"{name:<18} повтор {repeat}: "
            f"{elapsed:.3f} с, байт={result}"
        )

    return times, result


def main():
    print(f"URL: {len(URLS)}")
    print(f"Рабочих потоков/процессов: {WORKERS}")
    print(f"Повторов: {REPEATS}\n")

    sequential_times, expected = measure(
        "Последовательно", sequential
    )
    thread_times, _ = measure(
        "4 потока", with_threads, expected
    )
    process_times, _ = measure(
        "4 процесса", with_processes, expected
    )

    results = {
        "Последовательно": sequential_times,
        "4 потока": thread_times,
        "4 процесса": process_times,
    }

    print("\nИтоговая таблица")
    print(
        f"{'Способ':<18} {'Запуск 1':>10} {'Запуск 2':>10} "
        f"{'Запуск 3':>10} {'Медиана':>10}"
    )

    for name, times in results.items():
        median = statistics.median(times)
        print(
            f"{name:<18} "
            f"{times[0]:>9.3f}с "
            f"{times[1]:>9.3f}с "
            f"{times[2]:>9.3f}с "
            f"{median:>9.3f}с"
        )


if __name__ == "__main__":
    main()
