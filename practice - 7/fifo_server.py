import os
#!/usr/bin/env python3

import ast
import operator
import signal
import sys
from pathlib import Path

FIFO_DIRECTORY = Path("/tmp/lab7_ipc_zeus")
REQUEST_FIFO = FIFO_DIRECTORY / "request.fifo"
RESPONSE_FIFO = FIFO_DIRECTORY / "response.fifo"

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_node(node):
    if isinstance(node, ast.Expression):
        return evaluate_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Разрешены только числа")

    if isinstance(node, ast.BinOp):
        operation = BINARY_OPERATORS.get(
            type(node.op)
        )

        if operation is None:
            raise ValueError(
                "Эта операция запрещена"
            )

        left = evaluate_node(node.left)
        right = evaluate_node(node.right)

        if isinstance(node.op, ast.Pow):
            if abs(right) > 10:
                raise ValueError(
                    "Слишком большая степень"
                )

        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        operation = UNARY_OPERATORS.get(
            type(node.op)
        )

        if operation is None:
            raise ValueError(
                "Эта операция запрещена"
            )

        return operation(
            evaluate_node(node.operand)
        )

    raise ValueError(
        "Разрешены числа, скобки "
        "и арифметические операции"
    )


def safe_calculate(expression):
    if len(expression) > 200:
        raise ValueError(
            "Выражение слишком длинное"
        )

    tree = ast.parse(
        expression,
        mode="eval",
    )
    return evaluate_node(tree)


def remove_fifo(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def cleanup():
    remove_fifo(REQUEST_FIFO)
    remove_fifo(RESPONSE_FIFO)

    try:
        FIFO_DIRECTORY.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def handle_signal(signum, frame):
    print("\nПолучен сигнал, сервер завершается")
    raise SystemExit(0)


def send_response(message):
    # Открытие ожидает, пока клиент откроет
    # второй FIFO для чтения.
    with RESPONSE_FIFO.open(
        "w",
        encoding="utf-8",
    ) as response:
        response.write(message + "\n")
        response.flush()


def main():
    signal.signal(
        signal.SIGINT,
        handle_signal,
    )
    signal.signal(
        signal.SIGTERM,
        handle_signal,
    )

    cleanup()
    FIFO_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    os.mkfifo(REQUEST_FIFO)
    os.mkfifo(RESPONSE_FIFO)

    print("FIFO-сервер запущен")
    print("Канал запросов:", REQUEST_FIFO)
    print("Канал ответов:", RESPONSE_FIFO)
    print(
        "Для остановки отправьте запрос quit "
        "или нажмите Ctrl+C"
    )

    running = True

    try:
        while running:
            # После отключения клиента приходит EOF,
            # поэтому канал открывается заново.
            with REQUEST_FIFO.open(
                "r",
                encoding="utf-8",
            ) as request:
                for line in request:
                    expression = line.strip()

                    if not expression:
                        continue

                    print(
                        f"Получен запрос: "
                        f"{expression!r}"
                    )

                    if expression.lower() == "quit":
                        send_response(
                            "Сервер завершает работу"
                        )
                        running = False
                        break

                    try:
                        result = safe_calculate(
                            expression
                        )
                        answer = (
                            f"{expression} = {result}"
                        )
                    except Exception as error:
                        answer = (
                            f"Ошибка: "
                            f"{type(error).__name__}: "
                            f"{error}"
                        )

                    send_response(answer)
                    print(
                        f"Отправлен ответ: "
                        f"{answer!r}"
                    )
    finally:
        cleanup()
        print("FIFO удалены")


if __name__ == "__main__":
    main()
