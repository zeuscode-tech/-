#!/usr/bin/env python3
import gc
import os


def memory():
    values = {}
    with open("/proc/self/smaps_rollup") as file:
        for line in file:
            fields = line.split()
            if fields and fields[0] in (
                "Rss:", "Pss:", "Private_Dirty:"
            ):
                values[fields[0][:-1]] = int(fields[1])
    return values


def show(label, values):
    print(
        f"{label}: "
        f"RSS={values['Rss']} KiB, "
        f"PSS={values['Pss']} KiB, "
        f"Private_Dirty={values['Private_Dirty']} KiB",
        flush=True,
    )


def main():
    # Большой список ссылок: около 64 МБ на 64-битной системе.
    size = 8_000_000
    data = [None] * size
    gc.disable()

    print(f"Родитель PID={os.getpid()}, элементов={size}", flush=True)
    show("Родитель до fork", memory())

    pid = os.fork()

    if pid == 0:
        try:
            print(f"\nРебёнок PID={os.getpid()}", flush=True)
            before = memory()
            show("До изменения списка", before)

            # Меняем элементы существующего списка,
            # не создавая вместо него новый список.
            for index in range(size):
                data[index] = True

            after = memory()
            show("После изменения списка", after)

            print(
                "Разница: "
                f"RSS={after['Rss'] - before['Rss']:+d} KiB, "
                f"PSS={after['Pss'] - before['Pss']:+d} KiB, "
                "Private_Dirty="
                f"{after['Private_Dirty'] - before['Private_Dirty']:+d} KiB",
                flush=True,
            )
        except BaseException as error:
            print(f"Ошибка ребёнка: {error}", flush=True)
            os._exit(1)

        os._exit(0)

    # Родитель сохраняет свой список и ждёт ребёнка.
    _, status = os.waitpid(pid, 0)
    code = os.waitstatus_to_exitcode(status)
    print(f"\nРебёнок завершён, код={code}", flush=True)

    unchanged = all(value is None for value in data)
    print(f"Список родителя остался неизменным: {unchanged}", flush=True)

    return 0 if code == 0 and unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
