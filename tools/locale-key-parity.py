import json, glob, os, sys
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)
hay = {
    'index-src.html': open('index-src.html', encoding='utf-8').read(),
    'tools/build.py': open('tools/build.py', encoding='utf-8').read(),
}
locs = {os.path.basename(p)[:-5]: json.load(open(p, encoding='utf-8'))
        for p in sorted(glob.glob('src/locales/*.json'))}
en = locs['en']
allkeys = set().union(*[set(d) for d in locs.values()])

dead, uneven = [], []
import re as _re
for k in sorted(allkeys):
    alive = any(k in t for t in hay.values())
    if not alive:
        # composed names: shot1.alt is read as d[f"shot{n}.alt"]
        pat = _re.sub(r'\d+', lambda m: r'\{[^}]*\}', _re.escape(k))
        alive = any(_re.search(pat, t) for t in hay.values())
    if not alive:
        dead.append(k)
    have = [l for l, d in locs.items() if k in d]
    if len(have) != 9:
        uneven.append((k, len(have)))

print("keys:", len(allkeys), "dead:", len(dead), "uneven:", len(uneven))
for k in dead:
    print("  DEAD:", k, "| en:", repr(en.get(k))[:90])
for k, n in uneven:
    print("  UNEVEN:", k, n, "/9")
print("TOTAL", len(dead) + len(uneven))
