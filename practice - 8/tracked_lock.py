#!/usr/bin/env python3

import threading


class DeadlockDetected(RuntimeError):
    pass


class TrackedLock:
    _graph_mutex = threading.Lock()
    _locks = []
    _waiting = {}

    def __init__(self, name):
        self.name = name
        self._lock = threading.Lock()
        self.owner = None

        with TrackedLock._graph_mutex:
            TrackedLock._locks.append(self)

    @classmethod
    def reset_tracking(cls):
        with cls._graph_mutex:
            cls._locks.clear()
            cls._waiting.clear()

    @classmethod
    def _build_graph(cls):
        graph = {}

        for thread_name, awaited_lock in cls._waiting.items():
            owner = awaited_lock.owner

            if owner is not None:
                graph.setdefault(thread_name, set()).add(owner)
                graph.setdefault(owner, set())

        return graph

    @classmethod
    def _find_cycle(cls):
        graph = cls._build_graph()
        color = {
            node: 0
            for node in graph
        }
        stack = []
        position = {}

        def dfs(node):
            color[node] = 1
            position[node] = len(stack)
            stack.append(node)

            for neighbour in sorted(graph[node]):
                if color[neighbour] == 0:
                    cycle = dfs(neighbour)

                    if cycle is not None:
                        return cycle

                elif color[neighbour] == 1:
                    start = position[neighbour]
                    return stack[start:] + [neighbour]

            stack.pop()
            position.pop(node, None)
            color[node] = 2
            return None

        for node in sorted(graph):
            if color[node] == 0:
                cycle = dfs(node)

                if cycle is not None:
                    return cycle

        return None

    def acquire(self):
        current = threading.current_thread().name

        if self._lock.acquire(blocking=False):
            with TrackedLock._graph_mutex:
                self.owner = current
                TrackedLock._waiting.pop(current, None)

            return True

        with TrackedLock._graph_mutex:
            TrackedLock._waiting[current] = self
            cycle = TrackedLock._find_cycle()

            if cycle is not None:
                TrackedLock._waiting.pop(current, None)

                raise DeadlockDetected(
                    "Обнаружен цикл ожидания: "
                    + " -> ".join(cycle)
                )

            owner = self.owner
            print(
                f"{current}: ожидает {self.name}, "
                f"владелец={owner}",
                flush=True,
            )

        self._lock.acquire()

        with TrackedLock._graph_mutex:
            TrackedLock._waiting.pop(current, None)
            self.owner = current

        return True

    def release(self):
        current = threading.current_thread().name

        with TrackedLock._graph_mutex:
            if self.owner != current:
                raise RuntimeError(
                    f"{current} не является владельцем {self.name}"
                )

            self.owner = None

        self._lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.release()
        return False
