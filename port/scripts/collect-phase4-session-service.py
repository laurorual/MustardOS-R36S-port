#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read one stopped C11 generation through pinned SSH, public whitelist only."""
from pathlib import Path
import argparse,io,json,re,shlex,subprocess,tarfile
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('label');args=p.parse_args()
stage=args.stage.resolve();assert stage.is_relative_to(repo/'build/phase4/runtime-session');assert re.fullmatch(r'cycle[123]',args.label)
out=stage/args.label;out.mkdir(exist_ok=True);native=out/'native';native.mkdir(exist_ok=True)
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','root@192.168.15.17']
r=subprocess.run(ssh+['cat /run/muos/session/current'],capture_output=True,text=True,check=True);generation=r.stdout.strip();assert re.fullmatch(r'run-[0-9]{4}',generation);(out/'generation').write_text(generation+'\n');remote='/run/muos/session/'+generation
names=['report.txt','result','manager','profile-source.txt','profile-effective.txt','original-restored.txt','volume-before.sha256','volume-after.sha256','mixer-before.txt','mixer-after.txt','brightness-before.txt','brightness-after.txt','brightness-active.txt','drm-before.txt','drm-after.txt','software-volume.txt','mixer-active.txt','ui-identity.txt','ui-manager.txt','first-paint.txt','start.log','stop.log','restore.log','status.log','root-writers.txt','remount.txt','rng.txt']
code='set -eu; test -f '+remote+'/done; cd '+remote+'; set --; for name in '+' '.join(shlex.quote(n) for n in names)+'''; do
 [ -f "$name" ] || continue
 [ "$(stat -c %s "$name")" -le 524288 ]
 set -- "$@" "$name"
done
tar -cf - "$@"
'''
r=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=20);(out/'collection.tar').write_bytes(r.stdout);(out/'collection.stderr').write_bytes(r.stderr);assert r.returncode==0,r.stderr
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
 for m in t.getmembers():
  assert m.isfile() and m.name in names and m.size<=524288
  (native/m.name).write_bytes(t.extractfile(m).read())
r=subprocess.run(ssh+['tail -c 196608 '+remote+'/ui-start.txt'],capture_output=True);(native/'ui-start-tail.txt').write_bytes(r.stdout);assert r.returncode==0
r=subprocess.run(ssh+['sh -s'],input=(stage/'infrastructure-command.sh').read_text(),capture_output=True,text=True);(out/'infrastructure-after.txt').write_text(r.stdout);assert r.returncode==0
assert (stage/'infrastructure-before.txt').read_bytes()==(out/'infrastructure-after.txt').read_bytes()
health=r'''set -eu
/usr/libexec/muos-c07-network status; echo C07_NETWORK_OK
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro; echo ROOT_RO=1
! mountpoint -q /boot
printf 'TAINT='; cat /proc/sys/kernel/tainted
for n in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do ! pidof "$n" >/dev/null; done
echo NO_SESSION_PROCESSES
[ ! -S /run/dbus/system_bus_socket ]; echo NO_DBUS_SOCKET
[ -f /run/muos/entropy/stopped ] && [ ! -f /run/muos/entropy/ready ]; echo RNG_NOT_RELOADED
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\/O error|mmc.*timeout/ {n++} END{printf "KERNEL_ERROR_SIGNATURES=%d\n",n}'
'''
r=subprocess.run(ssh+['sh -s'],input=health,capture_output=True,text=True);(out/'health.txt').write_text(r.stdout);(out/'health.stderr').write_text(r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
pkg=(stage/'remote-directory').read_text().strip();assert re.fullmatch(r'/run/muos-c11\.[A-Za-z0-9]{6}',pkg)
r=subprocess.run(ssh+['sha256sum -c '+pkg+'/prerequisites.sha256'],capture_output=True,text=True);(out/'prerequisites-after.txt').write_text(r.stdout);assert r.returncode==0,r.stderr
print('C11 public generation collected; infrastructure unchanged, idle health/original hashes passed:',generation)
