#!/usr/bin/env python3

import threading
import time

PHILOSOPHERS = 5
MEALS_PER_PHILOSOPHER = 100


def run_simulation(strategy):
    forks = [
        threading.Lock()
        for _ in range(PHILOSOPHERS)
    ]

    table_limit = threading.Semaphore(
        PHILOSOPHERS - 1
    )

    start_barrier = threading.Barrier(PHILOSOPHERS)
    eaten = [0] * PHILOSOPHERS

    def eat_once(number, meal):
        left = number
        right = (number + 1) % PHILOSOPHERS

        if strategy == "ordered":
            first = min(left, right)
            second = max(left, right)

            with forks[first]:
                with forks[second]:
                    eaten[number] += 1

        elif strategy == "limited":
            # Одновременно вилки пытаются брать
            # не более четырёх философов.
            with table_limit:
                with forks[left]:
                    with forks[right]:
                        eaten[number] += 1

        else:
            raise ValueError(
                f"Неизвестная стратегия: {strategy}"
            )

        # Задержка только моделирует работу.
        # Она не является способом устранения deadlock.
        time.sleep(
            0.0001 * ((number + meal) % 3)
        )

    def philosopher(number):
        start_barrier.wait()

        for meal in range(MEALS_PER_PHILOSOPHER):
            eat_once(number, meal)

    threads = [
        threading.Thread(
            target=philosopher,
            name=f"Философ-{number}",
            args=(number,),
        )
        for number in range(PHILOSOPHERS)
    ]

    started = time.perf_counter()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=10)

    elapsed = time.perf_counter() - started
    alive = [
        thread.name
        for thread in threads
        if thread.is_alive()
    ]

    expected_total = (
        PHILOSOPHERS * MEALS_PER_PHILOSOPHER
    )
    actual_total = sum(eaten)

    print(f"Стратегия: {strategy}")

    for number, count in enumerate(eaten):
        print(
            f"Философ {number}: поел {count} раз"
        )

    print(f"Всего приёмов пищи: {actual_total}")
    print(f"Ожидалось: {expected_total}")
    print(f"Зависшие потоки: {alive}")
    print(
        "Каждый поел требуемое число раз: "
        f"{all(count == MEALS_PER_PHILOSOPHER for count in eaten)}"
    )
    print(
        "Взаимоблокировки нет: "
        f"{not alive}"
    )
    print(f"Время: {elapsed:.3f} с")
    print()

    if alive:
        raise RuntimeError(
            f"Обнаружены зависшие потоки: {alive}"
        )

    if actual_total != expected_total:
        raise RuntimeError(
            "Неверное количество приёмов пищи"
        )


def main():
    print("=== Исправление 1: нумерация вилок ===")
    print(
        "Каждый философ сначала берёт вилку "
        "с меньшим номером."
    )
    run_simulation("ordered")

    print(
        "=== Исправление 2: ограничение за столом ==="
    )
    print(
        "Семафор допускает к вилкам не более "
        "четырёх философов."
    )
    run_simulation("limited")


if __name__ == "__main__":
    main()
