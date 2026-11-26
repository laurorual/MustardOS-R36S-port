#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""M10: exact structural difference of two decompiled DTS files (dtc -O dts).

  dts-delta.py IN.dts OUT.dts   prints one line per difference:
    -node PATH | +node PATH | prop PATH NAME: OLD => NEW
Used by make-dtb-model.sh to prove a model DTB differs from dArkOSen's only
by the port's deltas."""
import re
import sys


def parse(path):
    nodes, stack = {}, []
    for line in open(path, encoding='utf-8'):
        s = line.strip()
        m = re.match(r'^([^\s=]+) \{$', s)
        if m:
            stack.append(m.group(1))
            nodes['/'.join(stack).replace('//', '/')] = {}
            continue
        if s == '};':
            stack.pop()
            continue
        m = re.match(r'^([^\s=]+)( = (.*))?;$', s)
        if m and stack:
            nodes['/'.join(stack).replace('//', '/')][m.group(1)] = m.group(3) or ''
    return nodes


a, b = parse(sys.argv[1]), parse(sys.argv[2])
for n in sorted(set(a) - set(b)):
    print('-node', n)
for n in sorted(set(b) - set(a)):
    print('+node', n)
for n in sorted(set(a) & set(b)):
    for k in sorted(set(a[n]) | set(b[n])):
        if a[n].get(k) != b[n].get(k):
            print(f'prop {n} {k}: {a[n].get(k, "<none>")} => {b[n].get(k, "<none>")}')
