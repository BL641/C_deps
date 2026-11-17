"""Граф зависимостей pip. Стандартная библиотека, без pip.

  python depvis.py --package A --repo testdata/chain.txt --test yes
      --output chain.svg --ascii no --depth 2 --filter - --reverse no
"""

import json
import re
import ssl
import sys
import urllib.error
import urllib.request

KEYS = ("package", "repo", "test", "output", "ascii", "depth", "filter", "reverse")


def fail(key, msg):
    print(f"ошибка: параметр {key}: {msg}", file=sys.stderr)
    raise SystemExit(2)


def yn(text, key):
    if text not in ("yes", "no"):
        fail(key, "допустимо только yes или no")
    return text == "yes"


def parse_cli(argv):
    if argv[1:] == ["-h"] or argv[1:] == ["--help"]:
        print("python depvis.py --package ИМЯ --repo АДРЕС --test yes|no --output ФАЙЛ.svg "
              "--ascii yes|no --depth N --filter ПОДСТРОКА --reverse yes|no")
        return None
    got, i = {}, 1
    while i < len(argv):
        arg = argv[i]
        if not arg.startswith("--") or arg == "--":
            fail(arg, "лишний аргумент")
        key = arg[2:]
        if key not in KEYS:
            fail(key, "неизвестный параметр")
        if key in got:
            fail(key, "параметр указан дважды")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            fail(key, "не указано значение")
        got[key] = argv[i + 1]
        i += 2
    for key in KEYS:
        if key not in got:
            fail(key, "параметр обязателен")
    cfg = {k: yn(got[k], k) for k in ("test", "ascii", "reverse")}
    cfg.update(package=got["package"], repo=got["repo"], output=got["output"])
    if cfg["test"]:
        if not re.fullmatch(r"[A-Z]+", cfg["package"]):
            fail("package", "в тестовом режиме имя состоит только из заглавных латинских букв")
    elif not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,197}[A-Za-z0-9])?", cfg["package"]):
        fail("package", "недопустимые символы в имени пакета")
    repo = cfg["repo"]
    if not repo or repo != repo.strip() or len(repo) >= 512:
        fail("repo", "пустое значение или пробелы по краям")
    if cfg["test"]:
        try:
            open(repo, "rb").close()
        except OSError:
            fail("repo", "файл тестового репозитория не найден: " + repo)
    elif not repo.startswith(("http://", "https://")) or " " in repo:
        fail("repo", "ожидается базовый адрес http(s), например https://pypi.org/pypi")
    elif repo.rstrip("/").endswith("/json"):
        fail("repo", "нужен базовый адрес репозитория, без имени пакета и суффикса /json")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,251}\.svg", cfg["output"]):
        fail("output", "нужно имя файла в текущем каталоге, заканчивающееся на .svg")
    if not got["depth"].isdigit() or int(got["depth"]) > 100:
        fail("depth", "нужно целое число от 0 до 100")
    cfg["depth"] = int(got["depth"])
    if got["filter"] == "-":
        cfg["filter"] = ""
    elif not re.fullmatch(r"[A-Za-z0-9._-]{1,50}", got["filter"]):
        fail("filter", "подстрока из букв, цифр и символов ._- длиной до 50; «-» отключает фильтр")
    else:
        cfg["filter"] = got["filter"]
    return cfg


def dep_name(req):
    body, sep, marker = req.partition(";")
    if sep and re.search(r"(?<![\w])extra(?![\w])", marker):
        return None
    body = re.split(r"\s*(?:===|==|~=|!=|<=|>=|<|>)\s*", body.split("[", 1)[0], maxsplit=1)[0]
    name = re.sub(r"[-_.]+", "-", body.strip().lower()).strip("-")
    return name if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name or "") else None


def http_get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "depvis/1.0"})
    last = None
    for ctx in (None, ssl._create_unverified_context()):
        try:
            with urllib.request.urlopen(request, timeout=30, context=ctx) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, b""
        except Exception as error:
            last = error
            if "CERTIFICATE_VERIFY_FAILED" not in str(error):
                break
    raise RuntimeError(last)


def fetch_deps(base, package):
    url = base.rstrip("/") + "/" + package + "/json"
    print(f"беру {package}\n{url}", file=sys.stderr)
    try:
        status, body = http_get(url)
    except Exception as error:
        print(f"не удалось получить пакет {package}: {error}", file=sys.stderr)
        return []
    if status != 200 or not body:
        print("пакет %s не найден" % package if status == 404 else "репозиторий вернул код %s для %s" % (status, package), file=sys.stderr)
        return []
    try:
        requires = (json.loads(body.decode("utf-8")).get("info") or {}).get("requires_dist") or []
    except Exception as error:
        print(f"не удалось разобрать пакет {package}: {error}", file=sys.stderr)
        return []
    found = []
    for item in requires:
        name = dep_name(item) if isinstance(item, str) else None
        if name and name not in found:
            found.append(name)
    return sorted(found)


def load_test(path):
    pkgs = {}
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        name, rest = (part.strip() for part in line.split(":", 1))
        deps = []
        for token in rest.split():
            if token not in deps:
                deps.append(token)
        pkgs[name] = sorted(set(deps))
    for deps in list(pkgs.values()):
        for name in deps:
            pkgs.setdefault(name, [])
    return pkgs


class Graph:
    def __init__(self):
        self.nodes, self.kids, self.edges, self.cycles = [], [], [], []
        self.rank, self.expanded, self.index = [], [], {}

    def node(self, name):
        if name not in self.index:
            self.index[name] = len(self.nodes)
            self.nodes.append(name)
            self.kids.append([])
            self.rank.append(-1)
            self.expanded.append(-1)
        return self.index[name]

    def link(self, parent, child, cycle):
        if child not in self.kids[parent]:
            self.kids[parent].append(child)
            self.edges.append((parent, child, cycle))


def dfs(graph, pkgs, cfg, net, node_id, depth, path):
    if depth >= cfg["depth"] or len(path) >= 120:
        return
    if 0 <= graph.expanded[node_id] <= depth:
        return
    graph.expanded[node_id] = graph.rank[node_id] = depth
    name = graph.nodes[node_id]
    if net and name not in pkgs:
        pkgs[name] = fetch_deps(cfg["repo"], name)
    for dep in pkgs.get(name, []):
        if cfg["filter"] and cfg["filter"] in dep:
            continue
        child = graph.node(dep)
        if graph.rank[child] < 0 or graph.rank[child] > depth + 1:
            graph.rank[child] = depth + 1
        seen = path.index(child) if child in path else -1
        graph.link(node_id, child, seen >= 0)
        if seen >= 0:
            line = " -> ".join(graph.nodes[i] for i in path[seen:] + [child])
            if line not in graph.cycles:
                graph.cycles.append(line)
            continue
        dfs(graph, pkgs, cfg, net, child, depth + 1, path + [child])


def analyze(pkgs, cfg, net):
    graph = Graph()
    root = graph.node(cfg["package"])
    graph.rank[root] = 0
    dfs(graph, pkgs, cfg, net, root, 0, [root])
    return graph


def reversed_pkgs(pkgs):
    rev = {name: [] for name in pkgs}
    for name, deps in pkgs.items():
        for dep in deps:
            rev.setdefault(dep, [])
            if name not in rev[dep]:
                rev[dep].append(name)
    return {name: sorted(deps) for name, deps in rev.items()}


def print_direct(deps, flt):
    print("Прямые зависимости:")
    if not deps:
        print("(нет)")
        return
    for name in deps:
        print(f"{name} (не войдёт в граф: фильтр)" if flt and flt in name else name)


def print_graph(graph):
    print("Рёбра графа:")
    print("\n".join(f"{graph.nodes[a]} -> {graph.nodes[b]}" for a, b, _ in graph.edges) or "(нет)")
    print("Циклы:")
    print("\n".join(graph.cycles) or "(нет)")
    print("Узлы: " + ", ".join(graph.nodes))


def print_tree(graph, root):
    print(root)

    def walk(node_id, prefix, stack, done):
        kids = graph.kids[node_id]
        for i, child in enumerate(kids):
            last = i + 1 == len(kids)
            print(prefix + ("└── " if last else "├── ") + graph.nodes[child], end="")
            if child in stack:
                print(" (цикл)")
                continue
            if done[child]:
                print(" (уже показан)")
                continue
            print()
            done[child] = True
            walk(child, prefix + ("    " if last else "│   "), stack + [child], done)

    if graph.nodes:
        done = [False] * len(graph.nodes)
        done[0] = True
        walk(0, "", [0], done)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "'")


def write_puml(graph, svg_name, root):
    path = svg_name[:-4] + ".puml"
    lines = ["@startuml", "left to right direction"]
    for i, name in enumerate(graph.nodes):
        lines.append(f'rectangle "{esc(name)}" as n{i}' + (" #ED8936" if name == root else ""))
    lines += [f"n{a} --> n{b}" for a, b, _ in graph.edges]
    lines.append("@enduml")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("PlantUML: " + path)


def write_svg(graph, path, root, depth):
    cols, max_rank = {}, 0
    for i, rank in enumerate(graph.rank):
        rank = 0 if rank < 0 else rank
        max_rank = max(max_rank, rank)
        cols.setdefault(rank, []).append(i)
    width = 36 + (max_rank + 1) * 180
    height = 70 + max((len(v) for v in cols.values()), default=1) * 56
    pos = {}
    for rank, ids in cols.items():
        for row, node_id in enumerate(ids):
            pos[node_id] = (36 + rank * 180, 56 + row * 56)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#f7fafc"/>',
        f'<text x="36" y="32" font-family="Arial" font-size="16">{esc(root)}, depth {depth}</text>',
    ]
    for a, b, cycle in graph.edges:
        x1, y1 = pos[a][0] + 120, pos[a][1] + 16
        x2, y2 = pos[b]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2 + 16}" stroke="{"#c53030" if cycle else "#2b6cb0"}"/>')
    for i, name in enumerate(graph.nodes):
        x, y = pos[i]
        fill = "#ed8936" if name == root else "#ebf8ff"
        parts.append(f'<rect x="{x}" y="{y}" width="120" height="32" rx="8" fill="{fill}" stroke="#2b6cb0"/>')
        parts.append(f'<text x="{x + 8}" y="{y + 21}" font-family="Arial" font-size="14">{esc(name)}</text>')
    parts.append("</svg>")
    open(path, "w", encoding="utf-8").write("\n".join(parts) + "\n")
    print(f"SVG: {path} ({len(graph.nodes)} узлов, {len(graph.edges)} рёбер)")


def main(argv):
    cfg = parse_cli(argv)
    if cfg is None:
        return 0
    print(f"package = {cfg['package']}\nrepo = {cfg['repo']}\n"
          f"test = {'yes' if cfg['test'] else 'no'}\noutput = {cfg['output']}\n"
          f"ascii = {'yes' if cfg['ascii'] else 'no'}\ndepth = {cfg['depth']}\n"
          f"filter = {cfg['filter'] or '-'}\nreverse = {'yes' if cfg['reverse'] else 'no'}")
    if cfg["reverse"] and not cfg["test"]:
        fail("reverse", "JSON API не содержит обратных зависимостей")
    pkgs = load_test(cfg["repo"]) if cfg["test"] else {}
    if not cfg["test"]:
        pkgs[cfg["package"]] = fetch_deps(cfg["repo"], cfg["package"])
    print_direct(pkgs.get(cfg["package"], []), cfg["filter"])
    graph = analyze(pkgs, cfg, not cfg["test"])
    print_graph(graph)
    if cfg["reverse"]:
        back = analyze(reversed_pkgs(pkgs), cfg, False)
        print("Обратные зависимости:")
        names = [name for name in back.nodes if name != cfg["package"]]
        print("\n".join(names) or "(нет)")
        print("Циклы среди обратных зависимостей:")
        print("\n".join(back.cycles) or "(нет)")
        if cfg["ascii"]:
            print("ASCII-дерево обратных зависимостей:")
            print_tree(back, cfg["package"])
    if cfg["ascii"]:
        print("ASCII-дерево зависимостей:")
        print_tree(graph, cfg["package"])
    write_puml(graph, cfg["output"], cfg["package"])
    write_svg(graph, cfg["output"], cfg["package"], cfg["depth"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
