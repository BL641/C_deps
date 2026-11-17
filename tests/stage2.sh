#!/bin/bash
# Этап 2. Прямые зависимости: тестовый файл и один пакет с PyPI.
cd "$(dirname "$0")"
py=python3

run() {
  echo
  echo "\$ $*"
  "$py" "$@"
}

echo "Этап 2. У A в chain.txt прямая зависимость только B, даже при глубине 2."
run depvis.py --package A --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 2 --filter - --reverse no

echo
echo "Этап 2. Прямые зависимости requests с PyPI. Нужен интернет."
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output requests.svg --ascii no --depth 1 --filter - --reverse no
