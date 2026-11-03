# python скрипт для взятия зависимостей
import importlib.metadata as md

def get_deps(package):
    try:
        requires = md.requires(package) or []
        deps = set()
        for req in requires:
            if 'extra' not in req :
                dep_name = req.split(';')[0].split('>')[0].split('<')[0].split('=')[0].strip().lower()
                deps.add(dep_name)
        return sorted(list(deps))
    except Exception:
        return []

def main():
    start_package = 'matplotlib'
    queue = [start_package]
    visited = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        
        visited.add(current)
        
        for dep in get_deps(current):
            if dep not in visited:
                print(f'    "{current}" -> "{dep}";')
                queue.append(dep)

if __name__ == "__main__":
    main()