#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Использование: $0 КАТАЛОГ ERROR|WARN [--top N]"
    echo "Пример: $0 data ERROR --top 3"
}

if (( $# == 0 )); then
    usage
    exit 1
fi

if (( $# != 2 && $# != 4 )); then
    usage >&2
    exit 1
fi

dir=$1
level=$2
top=0

if [[ ! -d "$dir" ]]; then
    echo "Ошибка: каталог не существует: $dir" >&2
    exit 1
fi

if [[ "$level" != ERROR && "$level" != WARN ]]; then
    echo "Ошибка: уровень должен быть ERROR или WARN" >&2
    exit 1
fi

if (( $# == 4 )); then
    if [[ "$3" != --top || ! "$4" =~ ^[1-9][0-9]*$ ]]; then
        echo "Ошибка: укажите --top N, где N — положительное целое" >&2
        exit 1
    fi
    top=$4
fi

# Относительный путь делаем однозначным для awk.
if [[ "$dir" != /* ]]; then
    dir="./$dir"
fi

shopt -s nullglob
files=("$dir"/*.log)

printf 'Модуль\tЧисло сообщений\n'

# При отсутствии журналов выводим только заголовок.
if (( ${#files[@]} == 0 )); then
    exit 0
fi

awk -v level="$level" '
    $3 == level && $4 ~ /^module=/ {
        module = $4
        sub(/^module=/, "", module)
        count[module]++
    }
    END {
        for (module in count)
            printf "%s\t%d\n", module, count[module]
    }
' "${files[@]}" |
    LC_ALL=C sort -k2,2nr -k1,1 |
    awk -v top="$top" 'top == 0 || NR <= top'
