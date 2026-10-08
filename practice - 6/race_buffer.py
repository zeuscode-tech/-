#!/usr/bin/env python3

import threading
import time
from collections import Counter

BUFFER_SIZE = 5
PRODUCER_COUNT = 3
CONSUMER_COUNT = 2
TOTAL_ITEMS = 1000

buffer = [None] * BUFFER_SIZE
write_index = 0
read_index = 0
item_count = 0

producers_done = threading.Event()

consumed_items = []
violation_examples = []
violation_count = 0

result_lock = threading.Lock()

minimum_count = 0
maximum_count = 0


def record_violation(message):
    global violation_count

    with result_lock:
        violation_count += 1

        # Чтобы журнал не стал слишком большим,
        # сохраняем только первые 20 примеров.
        if len(violation_examples) < 20:
            violation_examples.append(message)


def observe_count():
    global minimum_count, maximum_count

    with result_lock:
        minimum_count = min(
            minimum_count,
            item_count,
        )
        maximum_count = max(
            maximum_count,
            item_count,
        )


def producer(producer_id, items):
    global write_index, item_count

    for item in items:
        while item_count >= BUFFER_SIZE:
            time.sleep(0)

        # Эти операции должны быть одной критической
        # секцией, но блокировки здесь специально нет.
        slot = write_index
        time.sleep(0.00001)

        if buffer[slot] is not None:
            record_violation(
                f"Producer {producer_id}: "
                f"перезапись занятой ячейки {slot}"
            )

        buffer[slot] = item
        time.sleep(0.00001)

        write_index = (slot + 1) % BUFFER_SIZE
        time.sleep(0.00001)

        old_count = item_count
        time.sleep(0.00001)
        item_count = old_count + 1

        if item_count > BUFFER_SIZE:
            record_violation(
                f"Переполнение: count={item_count}"
            )

        observe_count()


def consumer(consumer_id):
    global read_index, item_count

    while True:
        if item_count <= 0:
            if producers_done.is_set():
                break

            time.sleep(0)
            continue

        # Эта операция тоже должна быть критической
        # секцией, но мьютекс отсутствует.
        slot = read_index
        time.sleep(0.00001)

        item = buffer[slot]
        time.sleep(0.00001)

        buffer[slot] = None
        read_index = (slot + 1) % BUFFER_SIZE
        time.sleep(0.00001)

        old_count = item_count
        time.sleep(0.00001)
        item_count = old_count - 1

        if item_count < 0:
            record_violation(
                f"Отрицательный count={item_count}"
            )

        observe_count()

        if item is None:
            record_violation(
                f"Consumer {consumer_id}: "
                f"прочитана пустая ячейка {slot}"
            )
        else:
            with result_lock:
                consumed_items.append(item)


def split_items():
    portions = [[] for _ in range(PRODUCER_COUNT)]

    for item in range(TOTAL_ITEMS):
        portions[item % PRODUCER_COUNT].append(item)

    return portions


def main():
    portions = split_items()

    consumers = [
        threading.Thread(
            target=consumer,
            args=(number,),
            name=f"consumer-{number}",
        )
        for number in range(CONSUMER_COUNT)
    ]

    producers = [
        threading.Thread(
            target=producer,
            args=(number, portions[number]),
            name=f"producer-{number}",
        )
        for number in range(PRODUCER_COUNT)
    ]

    started = time.perf_counter()

    for thread in consumers:
        thread.start()

    for thread in producers:
        thread.start()

    for thread in producers:
        thread.join()

    producers_done.set()

    for thread in consumers:
        thread.join(timeout=5)

        if thread.is_alive():
            record_violation(
                f"{thread.name} не завершился"
            )

    elapsed = time.perf_counter() - started

    counts = Counter(consumed_items)

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

    occupied_slots = sum(
        item is not None
        for item in buffer
    )

    exactly_once = (
        len(consumed_items) == TOTAL_ITEMS
        and not missing
        and not duplicates
    )

    buffer_valid = (
        minimum_count >= 0
        and maximum_count <= BUFFER_SIZE
        and occupied_slots == 0
    )

    print("=== Версия без синхронизации ===")
    print(f"Производителей: {PRODUCER_COUNT}")
    print(f"Потребителей: {CONSUMER_COUNT}")
    print(f"Размер буфера: {BUFFER_SIZE}")
    print(f"Создано элементов: {TOTAL_ITEMS}")
    print(f"Получено записей: {len(consumed_items)}")
    print(f"Пропущено элементов: {len(missing)}")
    print(f"Дубликатов: {len(duplicates)}")
    print(f"Осталось ячеек в буфере: {occupied_slots}")
    print(
        f"Диапазон count: "
        f"{minimum_count} ... {maximum_count}"
    )
    print(f"Нарушений обнаружено: {violation_count}")
    print(f"Каждый элемент ровно один раз: {exactly_once}")
    print(f"Инварианты буфера соблюдены: {buffer_valid}")
    print(f"Время: {elapsed:.3f} с")

    if violation_examples:
        print("\nПервые нарушения:")

        for message in violation_examples:
            print("-", message)


if __name__ == "__main__":
    main()
