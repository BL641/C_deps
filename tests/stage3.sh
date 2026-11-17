#!/bin/bash
# Этап 3. DFS: глубина, ромб, цикл, фильтр.
cd "$(dirname "$0")"
py=python3

run() {
  echo
  echo "\$ $*"
  "$py" "$@"
}

echo "Этап 3. chain.txt, глубина 1: только A -> B"
run depvis.py --package A --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 1 --filter - --reverse no

echo
echo "Этап 3. chain.txt, глубина 2: A -> B, B -> C"
run depvis.py --package A --repo testdata/chain.txt --test yes --output chain.svg --ascii no --depth 2 --filter - --reverse no

echo
echo "Этап 3. diamond.txt: A -> B, B -> D, A -> C, C -> D"
run depvis.py --package A --repo testdata/diamond.txt --test yes --output diamond.svg --ascii no --depth 3 --filter - --reverse no

echo
echo "Этап 3. cycle.txt: A -> B, B -> C, C -> B и цикл B -> C -> B"
run depvis.py --package A --repo testdata/cycle.txt --test yes --output cycle.svg --ascii yes --depth 5 --filter - --reverse no

echo
echo "Этап 3. filter.txt, подстрока X: AX не входит в рёбра"
run depvis.py --package A --repo testdata/filter.txt --test yes --output filter.svg --ascii no --depth 5 --filter X --reverse no
