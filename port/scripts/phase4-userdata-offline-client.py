#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Local deck-user client for the finite temporary C20 root helper."""
import argparse,json,socket

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['inspect','backup','resume','ack-backup','partition','format','repair-root-mode','verify','restore','stop'])
p.add_argument('--sha256');a=p.parse_args()
request={'action':a.action}
if a.action=='ack-backup':
    p.error('--sha256 is required') if a.sha256 is None else None
    request['sha256']=a.sha256
elif a.sha256 is not None:p.error('--sha256 is only valid with ack-backup')
with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
    s.settimeout(1200);s.connect('/run/muos-r35s-c20.sock')
    s.sendall((json.dumps(request)+'\n').encode());raw=b''
    while not raw.endswith(b'\n'):
        part=s.recv(65536)
        if not part or len(raw)+len(part)>4*1024*1024:raise SystemExit('Invalid helper response')
        raw+=part
response=json.loads(raw);print(json.dumps(response,indent=2))
raise SystemExit(0 if response['ok'] else 1)
