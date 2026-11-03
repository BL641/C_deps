import sys
import json
import urllib.request

def get_direct_deps(package):
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            requires = data["info"]["requires_dist"]
            if not requires:
                return []
            
            deps = set()
            for req in requires:
                if 'extra' in req:
                    continue
                dep_name = req.split(';')[0].split('>')[0].split('<')[0].split('=')[0].split('~')[0].strip().lower()
                if dep_name:
                    deps.add(dep_name)
            return list(deps)
    except Exception:
        return []

if __name__ == "__main__":
    pkg = sys.argv[1]
    deps = get_direct_deps(pkg)
    for d in deps:
        print(d)