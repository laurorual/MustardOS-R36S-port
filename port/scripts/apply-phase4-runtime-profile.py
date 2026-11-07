#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build-host post-overlay application of the reviewed profile. Never device init."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,stat,tempfile
parser=argparse.ArgumentParser();parser.add_argument('--target',type=Path,required=True);args=parser.parse_args()
root=args.target.resolve();assert root.is_dir() and root!=Path('/')
assert (root/'opt/muos/device/config/board/name').read_text().strip()=='rk-r35s-p0'
payload=root/'usr/share/muos-r35s-profile';assert payload.is_dir() and not payload.is_symlink()
meta=json.loads((payload/'manifest.json').read_text());profile=json.loads((payload/'profile.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert meta['profile_sha256']==sha(payload/'profile.json') and profile['board']=='rk-r35s-p0'
assert profile['model']=='R36S-V12 2023-08-18 Panel 0' and meta['ui_autostart'] is False
allowed={'etc/default/muos-core','etc/default/muos-ui','opt/muos/device/control/asound.state','opt/muos/share/hotkey/r35s-bringup.json'}
allowed.update('opt/muos/device/config/'+n for n in profile['device'])
allowed.update('opt/muos/config/'+n for n in profile['global'])
allowed.update('opt/muos/config/system/'+n for n in profile['system'])
allowed.update('opt/muos/share/theme/MustardOS/sound/'+n+'.wav' for n in ['navigate','info_open','info_close'])
assert set(meta['files'])==allowed
assert (payload/'overlay/etc/default/muos-ui').read_text()=='enabled=0\nhotkeys=1\n'
# Validate ALL files and parents before writing the first output.
for name,record in meta['files'].items():
 assert record['mode']==0o644
 p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
 source=payload/'overlay'/name;assert stat.S_ISREG(source.lstat().st_mode) and sha(source)==record['sha256']
 target=root/name
 for parent in target.parents:
  if parent==root:break
  assert not parent.is_symlink(),str(parent)
 assert not target.is_symlink()
 assert not target.exists() or target.is_file()
backup={};written=[]
try:
 for name,record in sorted(meta['files'].items()):
  target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
  backup[name]=(target.read_bytes(),stat.S_IMODE(target.stat().st_mode)) if target.exists() else None
  fd,tmp=tempfile.mkstemp(prefix='.muos-profile-',dir=target.parent)
  try:
   with os.fdopen(fd,'wb') as f:
    f.write((payload/'overlay'/name).read_bytes());f.flush();os.fchmod(f.fileno(),record['mode']);os.fsync(f.fileno())
   os.replace(tmp,target);written.append(name)
  finally:
   Path(tmp).unlink(missing_ok=True)
  assert sha(target)==record['sha256']
except BaseException:
 for name in reversed(written):
  target=root/name;old=backup[name]
  if old:target.write_bytes(old[0]);target.chmod(old[1])
  else:target.unlink()
 raise
assert (root/'etc/default/muos-ui').read_text()=='enabled=0\nhotkeys=1\n'
print('Reviewed Panel0 profile applied after overlay; UI remains disabled:',len(written),'files')
