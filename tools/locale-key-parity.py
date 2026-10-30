#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""locale-key-parity.py — ключи словарей: мёртвые и разъехавшиеся по языкам.

30.10.2026: прибор печатал вердикт, но ни разу не мог покраснеть — в файле не было
ни main(), ни sys.exit, поэтому мёртвый ключ и язык с 8 из 9 ключей давали код 0.
Для «прогнал и посмотрел глазами» этого хватало; для раннера (tools/check-all.py)
и любого `&&`-конвейера — нет: зелёный код возврата означал «скрипт дожил до конца»,
а не «соответствие есть». Теперь код возврата 1 при dead или uneven.
"""
import glob
import json
import os
import re
import sys


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    hay = {
        'index-src.html': open('index-src.html', encoding='utf-8').read(),
        'tools/build.py': open('tools/build.py', encoding='utf-8').read(),
    }
    locs = {os.path.basename(p)[:-5]: json.load(open(p, encoding='utf-8'))
            for p in sorted(glob.glob('src/locales/*.json'))}
    en = locs['en']
    allkeys = set().union(*[set(d) for d in locs.values()])

    dead, uneven = [], []
    for k in sorted(allkeys):
        alive = any(k in t for t in hay.values())
        if not alive:
            # composed names: shot1.alt is read as d[f"shot{n}.alt"]
            pat = re.sub(r'\d+', lambda m: r'\{[^}]*\}', re.escape(k))
            alive = any(re.search(pat, t) for t in hay.values())
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
    return 1 if (dead or uneven) else 0


if __name__ == '__main__':
    sys.exit(main())
