#!/bin/bash
# Этап 5. ASCII-дерево, PlantUML и SVG. Три пакета с PyPI.
cd "$(dirname "$0")"
py=python3

run() {
  echo
  echo "\$ $*"
  "$py" "$@"
}

echo "Этап 5. Три пакета, глубина 1. Нужен интернет."
echo "Появятся requests.svg, flask.svg, jinja2.svg и такие же файлы .puml."
run depvis.py --package requests --repo https://pypi.org/pypi --test no --output requests.svg --ascii yes --depth 1 --filter - --reverse no
run depvis.py --package flask --repo https://pypi.org/pypi --test no --output flask.svg --ascii yes --depth 1 --filter - --reverse no
run depvis.py --package jinja2 --repo https://pypi.org/pypi --test no --output jinja2.svg --ascii yes --depth 1 --filter - --reverse no

echo
echo "Картинки:"
ls -l requests.svg flask.svg jinja2.svg requests.puml flask.puml jinja2.puml
