#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C90 collect no-payload card readiness and recheck current protections."""
from pathlib import Path
import argparse,importlib,json,os,re,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require

prep=importlib.import_module('prepare-phase4-p2-card-readiness')
READ=r'''
from pathlib import Path
import json,os,re,stat,sys
root=Path(json.load(sys.stdin)['result']);assert re.fullmatch(r'/var/tmp/muos-r35s-c90-readiness\.[a-z0-9_]{8}',str(root))
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
assert {p.name for p in root.iterdir()}=={'analysis.json','journal'}
p=root/'journal';s=p.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
assert {p.name for p in p.iterdir()}=={'unlock-intent.json','complete.json'}
result={}
for name in ['analysis.json','journal/unlock-intent.json','journal/complete.json']:
 fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd);assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400 and 0<s.st_size<=65536
  data=os.read(fd,s.st_size+1);a=os.fstat(fd)
  assert len(data)==s.st_size and (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)
  result[name]=json.loads(data)
 finally:os.close(fd)
print(json.dumps(result))
'''

def validate(report,journal,manifest,kernel):
    require(report['passed'] is True and report['schema']==90 and report['operation']=='card-readiness-no-payload'
        and report['kernel']==kernel and report['source_sha256']==manifest['files'],'Readiness source/kernel binding')
    for n in ['exclusive_RDWR_opened_without_payload_write','whole_and_p2_transient_kernel_SETRO0',
        'all_four_aliases_kernel_readonly','p1_p3_readonly_during_transition','p2_512MiB_triple_hash_matches_C86','MBR_and_16MiB_boot_prefix_triple_verified']:
        require(report[n] is True,'Incomplete card readiness')
    for n in ['p3_full_content_hashed','physical_device_payload_written','candidate_provisioned_to_media',
        'boot_handoff_authorized','seed_generated_or_loaded','handoff_fence_created']:require(report[n] is False,'Unexpected physical action')
    require(set(journal)=={'unlock-intent','complete'},'No write intent permitted in readiness')
    start=journal['unlock-intent'];done=journal['complete']
    require(start['kind']=='CARD_READINESS_UNLOCK_MAY_HAVE_STARTED' and start['device_payload_write_allowed'] is False
        and start['p1_p3_must_remain_readonly'] is True,'Explicit no-payload unlock intent')
    require(done['kind']=='CARD_READINESS_VERIFIED' and all(done[n] is True for n in
        ['exclusive_RDWR_opened_without_payload_write','all_four_aliases_kernel_readonly',
        'p1_p3_readonly_during_transition','p2_and_MBR_and_boot_prefix_unchanged'])
        and done['physical_device_payload_written'] is False and done['boot_handoff_authorized'] is False,'Readiness completion journal')

def main(host,result):
    os.umask(0o077);require(re.fullmatch(r'/var/tmp/muos-r35s-c90-readiness\.[a-z0-9_]{8}',result),'Readiness result path')
    package=prep.prep.prep.latest(prep.AREA,'latest-package');p=json.loads((package/'analysis.json').read_text())
    require(p['passed'] is True and sha(package/'bundle/package.json')==p['package_manifest_sha256'],'Pinned readiness package')
    manifest=json.loads((package/'bundle/package.json').read_text());ctx=json.loads((package/'bundle/context.json').read_text())
    for n,h in manifest['files'].items():
        require(sha(package/'bundle'/n)==h,'Readiness bundle changed')
        if n.endswith('.py'):require(sha(prep.REPO/'port/scripts'/n)==h,'Deployed source changed')
    t=prep.prep.prep.transport();data=t.native(host,READ,json.dumps({'result':result}).encode())
    report=data['analysis.json'];journal={n:data['journal/'+n+'.json'] for n in ['unlock-intent','complete']}
    kernel=json.loads((prep.REPO/'dist/phase4/p2-controller/analysis.json').read_text())['kernel'];validate(report,journal,manifest,kernel)
    survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    protection=t.native(host,"from pathlib import Path; import json,platform,hashlib; s=Path('/sys/class/block'); p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((s/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    require(protection['kernel']==kernel and protection['guard']==ctx['automount_guard_sha256'] and set(protection['ro'].values())=={1},'Current card protection changed')
    stage=Path(tempfile.mkdtemp(prefix='copy.',dir=prep.AREA));(stage/'journal').mkdir(mode=0o700)
    for name,value in data.items():write_new(stage/name,(json.dumps(value,indent=2)+'\n').encode())
    ack={'passed':True,'schema':90,'remote_result':result,'package_manifest_sha256':p['package_manifest_sha256'],
        'native_receipt_sha256':sha(stage/'analysis.json'),'source_and_journal_verified':True,
        'native_MMC_RO_transition_qualified_without_payload':True,'current_all_RO_and_guard_verified':True,
        'physical_device_payload_written':False,'boot_handoff_authorized':False,'files':{n:sha(stage/n) for n in data}}
    for name,value in [('host-copy.json',ack),('inspection.json',survey),('protection.json',protection)]:write_new(stage/name,(json.dumps(value,indent=2)+'\n').encode())
    sync_dir(stage/'journal');sync_dir(stage);sync_dir(prep.AREA)
    (prep.AREA/'latest-complete').write_text(str(stage)+'\n');print('C90 native MMC readiness and unchanged p2/protection verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);p.add_argument('--result',required=True);a=p.parse_args();main(a.host,a.result)
