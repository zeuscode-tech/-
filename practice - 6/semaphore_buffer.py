#!/usr/bin/env python3

import threading
import time
from collections import Counter

BUFFER_SIZE = 5
PRODUCER_COUNT = 3
CONSUMER_COUNT = 2
TOTAL_ITEMS = 1000

STOP = object()


class RingBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = [None] * size
        self.write_index = 0
        self.read_index = 0
        self.count = 0

        # Сколько свободных ячеек.
        self.empty = threading.Semaphore(size)

        # Сколько занятых ячеек.
        self.full = threading.Semaphore(0)

        # Защита критической секции.
        self.mutex = threading.Lock()

        self.minimum_count = 0
        self.maximum_count = 0
        self.violations = []

    def check_invariants(self):
        if not 0 <= self.count <= self.size:
            self.violations.append(
                f"count вышел за границы: {self.count}"
            )

        occupied = sum(
            item is not None
            for item in self.buffer
        )

        if occupied != self.count:
            self.violations.append(
                f"occupied={occupied}, count={self.count}"
            )

        self.minimum_count = min(
            self.minimum_count,
            self.count,
        )
        self.maximum_count = max(
            self.maximum_count,
            self.count,
        )

    def put(self, item):
        # Ждём свободную ячейку.
        self.empty.acquire()

        try:
            with self.mutex:
                if self.buffer[self.write_index] is not None:
                    self.violations.append(
                        "Попытка перезаписать занятую ячейку "
                        f"{self.write_index}"
                    )

                self.buffer[self.write_index] = item
                self.write_index = (
                    self.write_index + 1
                ) % self.size
                self.count += 1

                self.check_invariants()
        finally:
            # Сообщаем, что появился элемент.
            self.full.release()

    def get(self):
        # Ждём готовый элемент.
        self.full.acquire()

        try:
            with self.mutex:
                item = self.buffer[self.read_index]

                if item is None:
                    self.violations.append(
                        "Попытка прочитать пустую ячейку "
                        f"{self.read_index}"
                    )

                self.buffer[self.read_index] = None
                self.read_index = (
                    self.read_index + 1
                ) % self.size
                self.count -= 1

                self.check_invariants()
        finally:
            # Сообщаем, что освободилась ячейка.
            self.empty.release()

        return item


def split_items():
    portions = [[] for _ in range(PRODUCER_COUNT)]

    for item in range(TOTAL_ITEMS):
        portions[item % PRODUCER_COUNT].append(item)

    return portions


def producer(producer_id, items, ring):
    for item in items:
        ring.put(item)

        if item % 100 == 0:
            time.sleep(0)


def consumer(consumer_id, ring, consumed, result_lock):
    while True:
        item = ring.get()

        if item is STOP:
            return

        with result_lock:
            consumed.append(item)

        if len(consumed) % 100 == 0:
            time.sleep(0)


def main():
    ring = RingBuffer(BUFFER_SIZE)
    consumed = []
    result_lock = threading.Lock()
    portions = split_items()

    producers = [
        threading.Thread(
            target=producer,
            args=(number, portions[number], ring),
            name=f"producer-{number}",
        )
        for number in range(PRODUCER_COUNT)
    ]

    consumers = [
        threading.Thread(
            target=consumer,
            args=(
                number,
                ring,
                consumed,
                result_lock,
            ),
            name=f"consumer-{number}",
        )
        for number in range(CONSUMER_COUNT)
    ]

    started = time.perf_counter()

    for thread in consumers:
        thread.start()

    for thread in producers:
        thread.start()

    for thread in producers:
        thread.join()

    # По одному маркеру остановки каждому потребителю.
    for _ in range(CONSUMER_COUNT):
        ring.put(STOP)

    for thread in consumers:
        thread.join()

    elapsed = time.perf_counter() - started

    counts = Counter(consumed)

    missing = [
        item
        for item in range(TOTAL_ITEMS)
        if counts[item] == 0
    ]

    duplicates = [
        item
        for item, number in counts.items()
        if number > 1
    ]

    occupied = sum(
        item is not None
        for item in ring.buffer
    )

    exactly_once = (
        len(consumed) == TOTAL_ITEMS
        and not missing
        and not duplicates
    )

    buffer_valid = (
        ring.minimum_count >= 0
        and ring.maximum_count <= BUFFER_SIZE
        and ring.count == 0
        and occupied == 0
        and not ring.violations
    )

    print("=== Семафоры и мьютекс ===")
    print(f"Производителей: {PRODUCER_COUNT}")
    print(f"Потребителей: {CONSUMER_COUNT}")
    print(f"Размер буфера: {BUFFER_SIZE}")
    print(f"Создано элементов: {TOTAL_ITEMS}")
    print(f"Потреблено элементов: {len(consumed)}")
    print(f"Пропущено: {len(missing)}")
    print(f"Дубликатов: {len(duplicates)}")
    print(f"Осталось в буфере: {ring.count}")
    print(
        f"Диапазон count: "
        f"{ring.minimum_count} ... "
        f"{ring.maximum_count}"
    )
    print(
        f"Нарушений инвариантов: "
        f"{len(ring.violations)}"
    )
    print(
        f"Каждый элемент ровно один раз: "
        f"{exactly_once}"
    )
    print(
        f"Инварианты буфера соблюдены: "
        f"{buffer_valid}"
    )
    print(f"Время: {elapsed:.3f} с")

    if ring.violations:
        print("\nПервые нарушения:")

        for message in ring.violations[:20]:
            print("-", message)


if __name__ == "__main__":
    main()

