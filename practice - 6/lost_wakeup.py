#!/usr/bin/env python3

import threading
import time


class BrokenBuffer:
    def __init__(self):
        self.item = None
        self.count = 0
        self.condition = threading.Condition()

        self.waiting_consumers = 0
        self.all_waiting = threading.Event()

        self.violations = []
        self.results = []

    def put(self, item):
        with self.condition:
            self.item = item
            self.count = 1

            print(
                "Производитель: добавил элемент",
                item,
            )

            # Будим сразу обоих потребителей,
            # хотя элемент только один.
            self.condition.notify_all()

    def get_broken(self, consumer_id):
        with self.condition:
            # ОШИБКА: if вместо while.
            if self.count == 0:
                self.waiting_consumers += 1

                print(
                    f"Потребитель {consumer_id}: "
                    "буфер пуст, засыпает"
                )

                if self.waiting_consumers == 2:
                    self.all_waiting.set()

                self.condition.wait()

            # После пробуждения условие повторно
            # не проверяется.
            value = self.item

            if self.count == 0 or value is None:
                message = (
                    f"Потребитель {consumer_id}: "
                    "проснулся, но буфер уже пуст"
                )
                self.violations.append(message)
                print("НАРУШЕНИЕ:", message)
            else:
                print(
                    f"Потребитель {consumer_id}: "
                    f"получил {value}"
                )

            self.item = None
            self.count -= 1
            self.results.append(
                (consumer_id, value)
            )


def main():
    buffer = BrokenBuffer()

    consumers = [
        threading.Thread(
            target=buffer.get_broken,
            args=(consumer_id,),
            name=f"consumer-{consumer_id}",
        )
        for consumer_id in range(2)
    ]

    for thread in consumers:
        thread.start()

    # Ждём, пока оба потребителя действительно
    # заснут внутри condition.wait().
    if not buffer.all_waiting.wait(timeout=2):
        raise RuntimeError(
            "Потребители не успели перейти в ожидание"
        )

    time.sleep(0.05)

    producer = threading.Thread(
        target=buffer.put,
        args=(42,),
        name="producer",
    )
    producer.start()
    producer.join()

    for thread in consumers:
        thread.join()

    print("\n=== Итог ===")
    print("Результаты потребителей:", buffer.results)
    print("Конечный count:", buffer.count)
    print(
        "Нарушений обнаружено:",
        len(buffer.violations),
    )
    print(
        "Корректность соблюдена:",
        not buffer.violations
        and buffer.count == 0,
    )

    print("\nПричина:")
    print(
        "notify_all разбудил двух потребителей, "
        "хотя в буфере был один элемент."
    )
    print(
        "Первый потребитель забрал элемент."
    )
    print(
        "Второй продолжил выполнение после if, "
        "не проверив условие повторно."
    )
    print(
        "С while второй потребитель снова увидел бы "
        "count == 0 и вернулся бы в wait()."
    )


if __name__ == "__main__":
    main()
