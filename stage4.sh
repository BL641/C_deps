#!/bin/bash
# Этап 4. Обратные зависимости пакета D в testdata/reverse.txt.
cd "$(dirname "$0")"
py=python3

run() {
  echo
  echo "\$ $*"
  "$py" "$@"
  echo "код выхода: $?"
}

echo "Этап 4. Глубина 1: B, C"
run depvis.py --package D --repo testdata/reverse.txt --test yes --output reverse.svg --ascii no --depth 1 --filter - --reverse yes

echo
echo "Этап 4. Глубина 2: B, A, C, E"
run depvis.py --package D --repo testdata/reverse.txt --test yes --output reverse.svg --ascii no --depth 2 --filter - --reverse yes

echo
echo "Этап 4. Глубина 3: B, A, F, C, E"
run depvis.py --package D --repo testdata/reverse.txt --test yes --output reverse.svg --ascii yes --depth 3 --filter - --reverse yes

echo
echo "Этап 4. На PyPI обратных зависимостей нет, ожидается ошибка."
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output a.svg --ascii no --depth 1 --filter - --reverse yes
