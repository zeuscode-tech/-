#!/usr/bin/env python3

import multiprocessing as mp
import os
import threading

shared_list = [1, 2, 3]


def thread_worker():
    print(
        f"Поток: PID={os.getpid()}, "
        f"Thread={threading.get_ident()}"
    )
    shared_list.append("из потока")
    print("Поток изменил список:", shared_list)


def process_worker():
    print(f"Дочерний процесс: PID={os.getpid()}")
    shared_list.append("из процесса")
    print("Процесс изменил свою копию:", shared_list)


def main():
    print(f"Родитель: PID={os.getpid()}")
    print("Исходный список:", shared_list)

    print("\n=== Поток ===")
    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()

    print("Родитель после потока:", shared_list)

    print("\n=== Процесс ===")
    context = mp.get_context("fork")
    process = context.Process(target=process_worker)
    process.start()
    process.join()

    print("Родитель после процесса:", shared_list)

    print("\nВывод:")
    print("- изменение из потока осталось в родительском списке;")
    print("- изменение из процесса в родительский список не попало.")


if __name__ == "__main__":
    main()
