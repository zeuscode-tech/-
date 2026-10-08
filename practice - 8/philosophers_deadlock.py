#!/usr/bin/env python3

import threading

PHILOSOPHERS = 5

forks = [
    threading.Lock()
    for _ in range(PHILOSOPHERS)
]

barrier = threading.Barrier(PHILOSOPHERS)


def philosopher(number):
    left = number
    right = (number + 1) % PHILOSOPHERS

    forks[left].acquire()

    print(
        f"Философ {number}: взял левую вилку {left}",
        flush=True,
    )

    # Все философы сначала должны взять левую вилку.
    barrier.wait()

    print(
        f"Философ {number}: ждёт правую вилку {right}",
        flush=True,
    )

    forks[right].acquire()

    # Эта строка при deadlock не будет достигнута.
    print(
        f"Философ {number}: начал есть",
        flush=True,
    )


def main():
    print("Запуск версии с взаимоблокировкой", flush=True)

    threads = [
        threading.Thread(
            target=philosopher,
            name=f"Философ-{number}",
            args=(number,),
        )
        for number in range(PHILOSOPHERS)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
