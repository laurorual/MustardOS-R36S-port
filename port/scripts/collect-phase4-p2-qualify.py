#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Collect C87 loop-only receipt/journals and recheck real-card RO state."""
from pathlib import Path
import argparse,importlib,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require,ROOT_OFFSET,ROOT_BYTES

prep=importlib.import_module('prepare-phase4-p2-qualify')
FETCH=r'''
from pathlib import Path
import os,re,stat,sys
root=Path(sys.argv[1]);name=sys.argv[2]
assert re.fullmatch(r'/var/tmp/muos-r35s-c87-qualify\.[a-z0-9_]{8}',str(root))
expected={'analysis.json','success','short-write'}
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
assert {p.name for p in root.iterdir()}==expected
allowed={'analysis.json','success/unlock-intent.json','success/write-intent.json','success/complete.json','short-write/unlock-intent.json','short-write/write-intent.json'}
assert name in allowed
for directory,leaves in [('success',{'unlock-intent.json','write-intent.json','complete.json'}),('short-write',{'unlock-intent.json','write-intent.json'})]:
 p=root/directory;s=p.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
 assert {p.name for p in p.iterdir()}==leaves
fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd);assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400 and 0<s.st_size<=65536
 data=os.read(fd,s.st_size+1);a=os.fstat(fd)
 assert len(data)==s.st_size and (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)
 sys.stdout.buffer.write(data)
finally:os.close(fd)
'''

def validate(report,manifest,journals):
    require(report['passed'] is True and report['schema']==87 and report['operation']=='qualify-loop-only','Qualification receipt')
    require(report['source_sha256']==manifest['files'],'Root snapshot source binding')
    for n in ['physical_card_payload_written','physical_card_SETRO0','physical_card_writer_entrypoint_available',
        'candidate_provisioned','boot_handoff_authorized','seed_generated_or_loaded']:require(report[n] is False,'Unexpected physical action')
    for n in ['physical_card_all_four_aliases_readonly','physical_card_p2_unchanged_since_C86',
        'physical_card_automount_guard_unchanged','loop_detached_and_large_fixture_files_removed']:require(report[n] is True,'Qualification incomplete')
    require(type(report['loop_case_count']) is int and report['loop_case_count']==len(report['cases'])==4
        and len(set(report['cases']))==4,'Loop cases incomplete')
    success=journals['success'];short=journals['short-write']
    require(set(success)=={'unlock-intent','write-intent','complete'} and set(short)=={'unlock-intent','write-intent'},'Journal completion inventory')
    for group in [success,short]:
        unlock=group['unlock-intent'];intent=group['write-intent']
        require(unlock['kind']=='P2_UNLOCK_MAY_HAVE_STARTED' and intent['kind']=='P2_WRITE_MAY_HAVE_STARTED','Journal event kinds')
        require(all(v['offset']==ROOT_OFFSET and v['bytes']==ROOT_BYTES for v in [unlock,intent]),'Journal bounded extent')
        for n in ['source_sha256','previous_sha256']:require(unlock[n]==intent[n],'Journal source/current binding')
        require(len(unlock['protected_sha256'])==2,'Protected complement binding')
    done=success['complete']
    require(done['kind']=='P2_WRITE_VERIFIED' and done['sha256']==success['unlock-intent']['source_sha256']
        and done['offset']==ROOT_OFFSET and done['bytes']==ROOT_BYTES,'Final journal readback')
    require(done['boot_handoff_authorized'] is False and all(done[n] is True for n in
        ['all_four_aliases_kernel_readonly','alias_cache_synchronized','protected_complement_verified']),'Completed protection')
    require(short['unlock-intent']['source_sha256']==short['unlock-intent']['previous_sha256']==done['sha256'],
        'Short-write fixture must start from the successful loop image')

def main(host,result):
    os.umask(0o077);require(re.fullmatch(r'/var/tmp/muos-r35s-c87-qualify\.[a-z0-9_]{8}',result),'Result path')
    package=prep.prep.latest(prep.AREA,'latest-package-qualify');pkg=json.loads((package/'analysis.json').read_text())
    require(pkg['passed'] is True and sha(package/'bundle/package.json')==pkg['package_manifest_sha256'],'Pinned package')
    manifest=json.loads((package/'bundle/package.json').read_text());ctx=json.loads((package/'bundle/context.json').read_text())
    for n,h in manifest['files'].items():require(sha(package/'bundle'/n)==h,'Package changed')
    for n,h in pkg['source_sha256'].items():require(sha(prep.REPO/n)==h,'Tested sources changed')
    stage=Path(tempfile.mkdtemp(prefix='copy-qualify.',dir=prep.AREA));t=prep.prep.transport()
    names=['analysis.json','success/unlock-intent.json','success/write-intent.json','success/complete.json',
        'short-write/unlock-intent.json','short-write/write-intent.json']
    for name in names:
        path=stage/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        p=subprocess.run(t.ssh(host)+[t.command(FETCH,result,name)],capture_output=True,timeout=30)
        require(p.returncode==0 and 0<len(p.stdout)<=65536,'Private result transfer failed')
        write_new(path,p.stdout)
    report=json.loads((stage/'analysis.json').read_text())
    journals={d:{p.stem:json.loads(p.read_text()) for p in (stage/d).iterdir()} for d in ['success','short-write']}
    validate(report,manifest,journals)
    inspection=t.native(host,t.INSPECT);t.validate_inspection(inspection)
    protection=t.native(host,"from pathlib import Path; import hashlib,json,platform; s=Path('/sys/class/block'); p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'kernel':platform.release(),'guard_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((s/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    require(protection['kernel']==report['kernel'] and protection['guard_sha256']==ctx['automount_guard_sha256']
        and set(protection['ro'].values())=={1},'Final real-card protection differs')
    acknowledgment={'passed':True,'schema':87,'remote_result':result,'package_manifest_sha256':sha(package/'bundle/package.json'),
        'native_receipt_sha256':sha(stage/'analysis.json'),'journals_bound_and_transfers_fsynced':True,
        'real_Valve_kernel_loop_test_validated':True,'real_card_all_four_aliases_RO_and_guard_verified':True,
        'physical_card_payload_written':False,'physical_card_SETRO0':False,'boot_handoff_authorized':False,
        'files':{n:sha(stage/n) for n in names}}
    for n,v in [('inspection.json',inspection),('protection.json',protection),('host-copy.json',acknowledgment)]:
        write_new(stage/n,(json.dumps(v,indent=2)+'\n').encode())
    sync_dir(stage);(prep.AREA/'latest-complete-qualify').write_text(str(stage)+'\n')
    print('C87 loop-only native qualification and card RO verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);p.add_argument('--result',required=True);a=p.parse_args();main(a.host,a.result)
