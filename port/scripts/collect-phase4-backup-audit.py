#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Collect the private diagnostic root image; never qualify it as a backup."""
from pathlib import Path
import argparse,importlib.util,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/offline-backup'
spec=importlib.util.spec_from_file_location('transport',repo/'port/scripts/run-phase4-offline-backup.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);args=p.parse_args();os.umask(0o077)
code=r'''
from pathlib import Path
import json,os,stat
results=[]
for root in Path('/var/tmp').glob('muos-r35s-c82-audit-result.????????'):
 s=root.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:continue
 p=root/'analysis.json'
 if p.is_symlink() or not p.is_file() or p.stat().st_size>65536:continue
 r=json.loads(p.read_text())
 if 'diagnostic_root_copy_sha256' in r:results.append({'directory':str(root),'report':r})
assert len(results)==1
print(json.dumps(results[0]))
'''
r=t.native(args.host,code);report=r['report'];assert report['diagnostic_only'] is True and report['backup_qualified'] is False
stage=Path(tempfile.mkdtemp(prefix='audit-native.',dir=area));write_new(stage/'diagnostic.json',(json.dumps(report,indent=2)+'\n').encode())
fetch=t.FETCH.replace('muos-r35s-c81-backup','muos-r35s-c82-audit-result')
with (stage/'root.partial.ext4').open('xb') as output:
 process=subprocess.run(t.ssh(args.host)+[t.command(fetch,r['directory'],'root.ext4')],stdout=output,stderr=subprocess.PIPE,timeout=600)
 output.flush();os.fsync(output.fileno())
assert process.returncode==0,process.stderr.decode(errors='replace')[-400:]
assert (stage/'root.partial.ext4').stat().st_size==512*1024*1024 and sha(stage/'root.partial.ext4')==report['diagnostic_root_copy_sha256']
sync_dir(stage)
write_new(stage/'analysis.json',(json.dumps({'passed':True,'diagnostic_only':True,'backup_qualified':False,'diagnostic_root_copy_verified':True,
 'offline_boot':report['offline_boot'],'plan_boot':report['plan_boot'],'remote_result':r['directory'],'source_sha256':sha(Path(__file__))},indent=2)+'\n').encode())
(area/'latest-native-audit').write_text(str(stage)+'\n')
print(json.dumps({k:report[k] for k in ['plan_boot','offline_boot','refusal','parents']},indent=2))
print('C82 partial root collected for private diagnosis only:',stage)
