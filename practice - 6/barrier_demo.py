#!/usr/bin/env python3

import threading
import time

THREAD_COUNT = 4
PHASE_COUNT = 3


class Barrier:
    def __init__(self, parties):
        self.parties = parties
        self.arrived = 0
        self.generation = 0
        self.condition = threading.Condition()

    def wait(self):
        with self.condition:
            current_generation = self.generation
            self.arrived += 1

            if self.arrived == self.parties:
                # Последний прибывший поток открывает барьер.
                self.arrived = 0
                self.generation += 1
                self.condition.notify_all()
                return

            # Защита от ложных и преждевременных
            # пробуждений.
            while current_generation == self.generation:
                self.condition.wait()


barrier = Barrier(THREAD_COUNT)

completed = [
    set()
    for _ in range(PHASE_COUNT)
]

violations = []
result_lock = threading.Lock()
print_lock = threading.Lock()


def safe_print(message):
    with print_lock:
        print(message)


def worker(thread_id):
    for phase in range(PHASE_COUNT):
        safe_print(
            f"Поток {thread_id}: "
            f"начал фазу {phase + 1}"
        )

        # Разная продолжительность работы потоков.
        delay = (
            0.03
            * ((thread_id + phase) % THREAD_COUNT)
        )
        time.sleep(delay)

        with result_lock:
            completed[phase].add(thread_id)

        safe_print(
            f"Поток {thread_id}: "
            f"завершил фазу {phase + 1}, "
            "ожидает остальных"
        )

        barrier.wait()

        # После барьера предыдущую фазу должны
        # завершить все четыре потока.
        with result_lock:
            completed_count = len(completed[phase])

            if completed_count != THREAD_COUNT:
                violations.append(
                    f"Поток {thread_id} прошёл "
                    f"фазу {phase + 1}, когда "
                    f"завершили только "
                    f"{completed_count} потоков"
                )

        safe_print(
            f"Поток {thread_id}: "
            f"прошёл барьер фазы {phase + 1}"
        )


def main():
    threads = [
        threading.Thread(
            target=worker,
            args=(thread_id,),
            name=f"worker-{thread_id}",
        )
        for thread_id in range(THREAD_COUNT)
    ]

    started = time.perf_counter()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    elapsed = time.perf_counter() - started

    print("\n=== Проверка барьера ===")

    for phase, thread_ids in enumerate(
        completed,
        start=1,
    ):
        print(
            f"Фаза {phase}: "
            f"завершили потоки "
            f"{sorted(thread_ids)}"
        )

    print(
        f"Нарушений: {len(violations)}"
    )
    print(
        "Все фазы выполнены корректно:",
        all(
            len(thread_ids) == THREAD_COUNT
            for thread_ids in completed
        )
        and not violations,
    )
    print(f"Время: {elapsed:.3f} с")

    if violations:
        print("\nОбнаруженные нарушения:")

        for message in violations:
            print("-", message)


if __name__ == "__main__":
    main()
