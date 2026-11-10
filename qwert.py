import sys
import json
import urllib.request

def get_direct_deps(package):
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            requires = data["info"].get("requires_dist")
            if not requires:
                return []

            deps = set()
            for req in requires:
                
                if 'extra' in req:
                    continue

                
                dep_name = req.split(';')[0]

              
                for sep in ('>=', '<=', '==', '!=', '~=', '>', '<', '='):
                    dep_name = dep_name.split(sep)[0]

                
                dep_name = dep_name.split('[')[0].strip().lower()

                if dep_name:
                    deps.add(dep_name)
            return sorted(deps)
    except Exception as e:
        
        print(f"[qwert.py] error for {package}: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    pkg = sys.argv[1]
    for d in get_direct_deps(pkg):
        print(d)