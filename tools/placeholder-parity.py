#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""placeholder-parity.py — плейсхолдеры {name} по языкам и их протечки на страницы.

30.10.2026: как и у locale-key-parity.py, здесь не было ни main(), ни sys.exit —
«MISMATCHED 0» и «LEAKS 0» печатались, а код возврата всегда был 0. Перепутанный
плейсхолдер (в языке missing ['n'], extra ['количество']) и незакрытая фигурная
скобка на живой странице считались зелёными для любого раннера. Теперь код 1,
если есть mismatch или leak.
"""
import glob
import json
import os
import re
import sys


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    locs = {os.path.basename(p)[:-5]: json.load(open(p, encoding='utf-8'))
            for p in sorted(glob.glob('src/locales/*.json'))}
    PH = re.compile(r'\{([A-Za-z0-9_]+)\}')
    en = locs['en']

    print("=== placeholders per key (en) ===")
    carriers = 0
    for k in sorted(en):
        if isinstance(en[k], str):
            s = set(PH.findall(en[k]))
            if s:
                carriers += 1
                print(f"  {k:22} {sorted(s)}")
    print("carrier keys:", carriers)

    print("=== mismatches vs en ===")
    bad = 0
    for lang, d in locs.items():
        if lang == 'en':
            continue
        for k, v in d.items():
            if not isinstance(v, str) or not isinstance(en.get(k), str):
                continue
            want, got = set(PH.findall(en[k])), set(PH.findall(v))
            if want != got:
                bad += 1
                print(f"  {lang}/{k}: missing={sorted(want-got)} extra={sorted(got-want)}")
    print("MISMATCHED", bad)

    # leaked placeholders in built pages
    print("=== leaked '{' in built pages ===")
    leak = 0
    for f in ['index.html'] + [f"{l}/index.html" for l in locs if l != 'en']:
        t = open(f, encoding='utf-8').read()
        for m in set(PH.findall(t)):
            leak += 1
            print("  ", f, m)
    print("LEAKS", leak)
    return 1 if (bad or leak) else 0


if __name__ == '__main__':
    sys.exit(main())
