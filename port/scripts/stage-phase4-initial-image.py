#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage C88 as a private regular file on Deck. Never open or write media."""
from pathlib import Path
import argparse,importlib,json,os,subprocess
from phase4_backup_core import sha,write_new
from phase4_root_migration import require,ROOT_BYTES
import phase4_recovery_image as image

prep=importlib.import_module('prepare-phase4-initial-image')
RECEIVE=r'''
from pathlib import Path
import hashlib,json,os,re,shutil,stat,subprocess,sys,tempfile
os.umask(0o077);expected=sys.argv[1];counter=int(sys.argv[2]);size=512*1024*1024
assert re.fullmatch('[0-9a-f]{64}',expected) and 1<=counter<=9998
parent=Path('/home/deck');s=parent.lstat()
assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and not s.st_mode&0o022
fs=subprocess.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN'],capture_output=True,text=True,check=True).stdout.split()
nums={(p/'dev').read_text().strip() for p in Path('/sys/class/block').glob('mmcblk*') if (p/'dev').is_file()}
assert len(fs)==2 and fs[0] in ('btrfs','ext4') and fs[1] not in nums
assert shutil.disk_usage(parent).free>=1024**3
stage=Path(tempfile.mkdtemp(prefix='muos-r35s-c88-candidate.',dir=parent));stage.chmod(0o700)
target=stage/'candidate.ext4';fd=os.open(target,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
try:
 h=hashlib.sha256();position=0
 while position<size:
  count=min(1024*1024,size-position);data=bytearray()
  while len(data)<count:
   block=sys.stdin.buffer.read(count-len(data));assert block,'Short image transport'
   data.extend(block)
  h.update(data)
  if data!=bytes(count):assert os.pwrite(fd,data,position)==count
  position+=count
 assert not sys.stdin.buffer.read(1) and h.hexdigest()==expected
 os.ftruncate(fd,size);os.fsync(fd)
 h=hashlib.sha256()
 for offset in range(0,size,1024*1024):
  data=os.pread(fd,1024*1024,offset);assert len(data)==1024*1024;h.update(data)
 s=os.fstat(fd);assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and s.st_size==size and stat.S_IMODE(s.st_mode)==0o600
 assert h.hexdigest()==expected
finally:os.close(fd)
report={'passed':True,'schema':88,'stage':str(stage),'candidate_sha256':expected,'bytes':size,'counter':counter,
 'stream_and_independent_readback_sha256_verified':True,'private_regular_file_only':True,
 'physical_media_opened_or_written':False,'boot_handoff_authorized':False,'handoff_fence_created':False}
with (stage/'staged.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
for p in [stage,parent]:
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);os.fsync(fd);os.close(fd)
print(json.dumps(report))
'''

def main(host):
    os.umask(0o077);stage=prep.prep.prep.latest(prep.AREA,'latest-complete')
    host_report=json.loads((stage/'host-analysis.json').read_text());r=json.loads((stage/'analysis.json').read_text())
    require(host_report['passed'] is True and sha(stage/'analysis.json')==host_report['consumer_analysis_sha256'],'Completed C88 source')
    for n,h in host_report['source_sha256'].items():require(sha(prep.REPO/n)==h,'Provisioned source changed')
    require(not (stage/'deck-stage.json').exists(),'Candidate already staged; inspect existing copy')
    t=prep.prep.prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    protection=t.native(host,"from pathlib import Path; import json; s=Path('/sys/class/block'); print(json.dumps({n:int((s/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}))")
    require(set(protection.values())=={1},'Card RO must remain active while staging')
    with image.source_image(stage/'candidate.ext4',r['candidate_sha256'],ROOT_BYTES) as fd:
        p=subprocess.run(t.ssh(host)+[t.command(RECEIVE,r['candidate_sha256'],r['counter_preserved'])],stdin=fd,capture_output=True,timeout=600)
    write_new(stage/'deck-stage.stderr',p.stderr)
    require(p.returncode==0,'Private Deck staging failed; keep partial, do not auto retry')
    receipt=json.loads(p.stdout)
    require(receipt['passed'] is True and receipt['candidate_sha256']==r['candidate_sha256'] and receipt['bytes']==ROOT_BYTES
        and receipt['physical_media_opened_or_written'] is False and receipt['boot_handoff_authorized'] is False,'Staging receipt')
    write_new(stage/'deck-stage.json',(json.dumps(receipt,indent=2)+'\n').encode())
    print('C88 candidate staged as private regular file; no media write:',receipt['stage'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);a=p.parse_args();main(a.host)
