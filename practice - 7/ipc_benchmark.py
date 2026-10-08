#!/usr/bin/env python3

import multiprocessing as mp
import statistics
import time
from array import array
from multiprocessing import shared_memory

COUNT = 10_000_000
REPEATS = 3


def pipe_receiver(connection):
    """Получает весь массив через Pipe."""
    payload = connection.recv_bytes()
    values = memoryview(payload).cast("I")
    checksum = sum(values)
    values.release()

    connection.send(checksum)
    connection.close()


def shared_memory_receiver(name, byte_count, ready, result_connection):
    """Читает массив непосредственно из общей памяти."""
    memory = shared_memory.SharedMemory(name=name)

    try:
        ready.wait()

        values = memory.buf[:byte_count].cast("I")
        checksum = sum(values)
        values.release()

        result_connection.send(checksum)
    finally:
        result_connection.close()
        memory.close()


def benchmark_pipe(payload):
    parent_connection, child_connection = mp.Pipe(duplex=True)

    process = mp.Process(
        target=pipe_receiver,
        args=(child_connection,),
    )

    started = time.perf_counter()
    process.start()
    child_connection.close()

    parent_connection.send_bytes(payload)
    checksum = parent_connection.recv()

    process.join()
    elapsed = time.perf_counter() - started
    parent_connection.close()

    return elapsed, checksum


def benchmark_shared_memory(payload):
    memory = shared_memory.SharedMemory(create=True, size=len(payload))
    ready = mp.Event()
    parent_connection, child_connection = mp.Pipe(duplex=False)

    process = mp.Process(
        target=shared_memory_receiver,
        args=(memory.name, len(payload), ready, child_connection),
    )

    try:
        started = time.perf_counter()
        process.start()
        child_connection.close()

        memory.buf[:len(payload)] = payload
        ready.set()

        checksum = parent_connection.recv()
        process.join()
        elapsed = time.perf_counter() - started

        return elapsed, checksum
    finally:
        parent_connection.close()
        memory.close()
        memory.unlink()


def main():
    print(f"Подготовка массива из {COUNT:,} чисел...")

    numbers = array("I", (index % 1000 for index in range(COUNT)))

    if numbers.itemsize != 4:
        raise RuntimeError("Для теста требуется четырёхбайтовый тип I")

    payload = numbers.tobytes()
    expected_checksum = sum(numbers)
    size_mib = len(payload) / 1024 / 1024

    print(f"Объём данных: {size_mib:.1f} МиБ")
    print(f"Контрольная сумма: {expected_checksum}")
    print(f"Повторов: {REPEATS}")
    print()

    pipe_times = []
    shared_times = []

    for repeat in range(1, REPEATS + 1):
        elapsed, checksum = benchmark_pipe(payload)
        assert checksum == expected_checksum

        pipe_times.append(elapsed)
        print(
            f"Pipe          повтор {repeat}: "
            f"{elapsed:.3f} с, сумма={checksum}"
        )

    print()

    for repeat in range(1, REPEATS + 1):
        elapsed, checksum = benchmark_shared_memory(payload)
        assert checksum == expected_checksum

        shared_times.append(elapsed)
        print(
            f"Shared memory повтор {repeat}: "
            f"{elapsed:.3f} с, сумма={checksum}"
        )

    pipe_median = statistics.median(pipe_times)
    shared_median = statistics.median(shared_times)

    print()
    print("Итоговая таблица")
    print(f"{'Механизм':<18} {'Запуск 1':>10} {'Запуск 2':>10} "
          f"{'Запуск 3':>10} {'Медиана':>10}")

    print(
        f"{'Pipe':<18}"
        f"{pipe_times[0]:>9.3f}с"
        f"{pipe_times[1]:>9.3f}с"
        f"{pipe_times[2]:>9.3f}с"
        f"{pipe_median:>9.3f}с"
    )

    print(
        f"{'Shared memory':<18}"
        f"{shared_times[0]:>9.3f}с"
        f"{shared_times[1]:>9.3f}с"
        f"{shared_times[2]:>9.3f}с"
        f"{shared_median:>9.3f}с"
    )

    print()
    print(
        "Ускорение shared memory относительно Pipe: "
        f"{pipe_median / shared_median:.2f} раза"
    )
    print("Все контрольные суммы совпали: True")


if __name__ == "__main__":
    main()
