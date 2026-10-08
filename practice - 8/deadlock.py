#!/usr/bin/env python3

import threading
import time

from tracked_lock import DeadlockDetected, TrackedLock


def worker(first_lock, second_lock, barrier):
    name = threading.current_thread().name

    try:
        with first_lock:
            print(
                f"{name}: захватил {first_lock.name}",
                flush=True,
            )

            barrier.wait()
            time.sleep(0.05)

            print(
                f"{name}: пытается захватить "
                f"{second_lock.name}",
                flush=True,
            )

            try:
                with second_lock:
                    print(
                        f"{name}: захватил оба ресурса",
                        flush=True,
                    )
            except DeadlockDetected as error:
                print(
                    f"{name}: {error}",
                    flush=True,
                )

    except Exception as error:
        print(
            f"{name}: ошибка: {error}",
            flush=True,
        )


def main():
    TrackedLock.reset_tracking()

    lock_a = TrackedLock("Lock-A")
    lock_b = TrackedLock("Lock-B")
    barrier = threading.Barrier(2)

    thread_1 = threading.Thread(
        target=worker,
        name="Поток-1",
        args=(lock_a, lock_b, barrier),
    )

    thread_2 = threading.Thread(
        target=worker,
        name="Поток-2",
        args=(lock_b, lock_a, barrier),
    )

    print("Запуск двух потоков с обратным порядком блокировок")
    print()

    thread_1.start()
    thread_2.start()

    thread_1.join(timeout=3)
    thread_2.join(timeout=3)

    print()
    print("=== Итог ===")
    print(f"Поток-1 завершён: {not thread_1.is_alive()}")
    print(f"Поток-2 завершён: {not thread_2.is_alive()}")
    print(
        "Зависших потоков: "
        f"{int(thread_1.is_alive()) + int(thread_2.is_alive())}"
    )

    if thread_1.is_alive() or thread_2.is_alive():
        raise RuntimeError("Потоки неожиданно зависли")

    print(
        "TrackedLock обнаружил цикл до возникновения "
        "вечного ожидания."
    )


if __name__ == "__main__":
    main()
