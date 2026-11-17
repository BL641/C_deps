#!/bin/bash
# Этап 1. Печать параметров и ошибка на каждый из них.
cd "$(dirname "$0")"
py=python3

run() {
  echo
  echo "\$ $*"
  "$py" "$@"
  echo "код выхода: $?"
}

echo "Этап 1. Успешный запуск печатает параметры и ничего не скачивает."
run depvis.py --package A --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 1 --filter - --reverse no

echo
echo "Этап 1. Ошибки параметров."
run depvis.py --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 1 --filter - --reverse no
run depvis.py --package Ab --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 1 --filter - --reverse no
run depvis.py --package A --repo testdata/missing.txt --test yes --output chain.svg --ascii no --depth 1 --filter - --reverse no
run depvis.py --package requests --repo pypi.org/pypi --test no --output a.svg --ascii no --depth 1 --filter - --reverse no
run depvis.py --package requests --repo https://pypi.org/pypi --test maybe --output a.svg --ascii no --depth 1 --filter - --reverse no
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output graph.png --ascii no --depth 1 --filter - --reverse no
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output a.svg --ascii true --depth 1 --filter - --reverse no
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output a.svg --ascii no --depth -1 --filter - --reverse no
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output a.svg --ascii no --depth 1 --filter "a b" --reverse no
run depvis.py --package A --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 1 --filter - --reverse maybe
