#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C95 pinned protection-only package and independent current preimage copy."""
from pathlib import Path
import argparse,base64,importlib,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums
import phase4_root_recovery as recovery
import phase4_root_metadata as metadata

initial=importlib.import_module('prepare-phase4-initial-migration')
old=importlib.import_module('prepare-phase4-root-permissions')
helper=importlib.import_module('phase4-card-rearm')
REPO=initial.REPO;WORK=initial.WORK;AREA=WORK/'card-rearm'
FETCH=r'''
from pathlib import Path
import os,re,stat,sys
root=Path(sys.argv[1]);name=sys.argv[2]
assert re.fullmatch(r'/var/tmp/muos-r35s-c95-protect\.[a-z0-9_]{8}',str(root))
names={'analysis.json','current-prefix.backup',*[f'p{n}-{k}.bin' for n in (2,3) for k in ['sb','gd','sector']]}
assert name in names
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 before=os.fstat(fd);limit=640*1024*1024 if name=='current-prefix.backup' else 1024*1024
 assert stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o400 and 0<before.st_size<=limit
 if name=='current-prefix.backup':assert before.st_size==limit
 remaining=before.st_size
 while remaining:
  raw=os.read(fd,min(1024*1024,remaining));assert raw;remaining-=len(raw);sys.stdout.buffer.write(raw)
 after=os.fstat(fd);assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
finally:os.close(fd)
'''

def validate_report(r,ctx,manifest):
    require(r['passed'] is True and type(r['schema']) is int and r['schema']==95 and r['operation']=='protect-and-capture','Protection-only native result')
    require(r['context_sha256']==recovery.hashed(recovery.encoded(ctx)) and r['source_sha256']==manifest['files'],'Root payload/context binding')
    require(r['runtime_guard_sha256']==ctx['runtime_guard_sha256'] and r['boot_sequence']==ctx['expected_boot_sequence'] and
        r['attempt_sha256']==ctx['attempt_sha256'] and type(r['prefix_bytes']) is int and r['prefix_bytes']==640*1024*1024,
        'Current state/guard/fence/size binding')
    require(r['root_modes']=={'p2':0o777,'p3':0o777} and r['p2_fsck_exit']==r['p3_fsck_exit']==0,'Observed root modes/fsck')
    for n in ['historical_independent_backup_reverified','userdata_matches_C82','all_four_aliases_kernel_readonly','runtime_guard_restored_or_reverified']:
        require(r[n] is True,'Protection incomplete')
    for n in ['physical_payload_written','media_unlocked','seed_loaded_or_generated','repair_applied']:require(r[n] is False,'Unexpected payload operation')
    recovery.digest(r['current_prefix_sha256'])

def prepare(host,boot):
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    checks=initial.latest(AREA,'latest-checks');c=json.loads((checks/'analysis.json').read_text());require(c['passed'] is True,'C95 checks required')
    for n,h in c['source_sha256'].items():require(sha(REPO/n)==h,'Tested C95 source changed')
    for name in ['root-permissions','p2-initial-prepared','p2-recovery-native','p2-recovery-boot']:
        root=REPO/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Frozen parent proof changed')
    held,ack,attempt,known,_=initial.held_recovery();require(type(boot) is int and known<=boot<=9998,'Known observed boot')
    previous=initial.latest(WORK/'root-permissions','latest-complete');a=json.loads((previous/'host-copy.json').read_text())
    require(a['passed'] is True,'Historical C83 independent capsule')
    for n,h in a['files'].items():require(sha(previous/n)==h,'C83 artifact changed')
    prior=json.loads((previous/'analysis.json').read_text());legacy=json.loads((previous/'context.json').read_text())
    ctx={'schema':95,'operation':'protect-and-capture','legacy_context':legacy,'runtime_guard_sha256':prior['automount_guard_sha256'],
        'expected_boot_sequence':boot,'attempt_sha256':ack['next_attempt_sha256']}
    helper.validate_context(ctx,importlib.import_module('phase4_root_migration'))
    t=old.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    rule=t.native(host,"from pathlib import Path; import hashlib,json; p=Path('/usr/lib/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))")
    require(rule['source_sha256']==legacy['automount_rule_sha256'],'SteamOS rule changed; no automatic substitution')
    write_new(AREA/'protect-package.claim',b'C95 package may be deployed; inspect partial before replacement\n');sync_dir(AREA)
    package=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));bundle=package/'bundle';bundle.mkdir(mode=0o700)
    for name in helper.SOURCES-{'context.json'}:write_new(bundle/name,(REPO/'port/scripts'/name).read_bytes())
    write_new(bundle/'context.json',recovery.encoded(ctx));manifest={'operation':'protect-and-capture','files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',recovery.encoded(manifest));target='/home/deck/muos-r35s-c95-protect-'+sha(bundle/'package.json')[:12]
    original="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')",'Path('+repr(target)+')').replace(original,repr(helper.SOURCES|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    result=t.native(host,code,json.dumps({'files':files}).encode())
    require(result['passed'] is True and result['helper_started'] is False and result['files']==manifest['files']|{'package.json':sha(bundle/'package.json')},'Finite deployment readback')
    write_new(package/'analysis.json',recovery.encoded({'passed':True,'target':target,'manifest_sha256':sha(bundle/'package.json'),
        'checks_sha256':sha(checks/'analysis.json'),'held_recovery':str(held),'card_payload_written':False,'sudo_started':False}))
    sync_dir(package);(AREA/'latest-package').write_text(str(package)+'\n');sync_dir(AREA)
    print('C95 protection package verified:',package)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-card-rearm.py protect')

def collect(host,result):
    os.umask(0o077);require(re.fullmatch(r'/var/tmp/muos-r35s-c95-protect\.[a-z0-9_]{8}',result),'Finite protected result path')
    package=initial.latest(AREA,'latest-package');p=json.loads((package/'analysis.json').read_text());bundle=package/'bundle'
    require(p['passed'] is True and sha(bundle/'package.json')==p['manifest_sha256'],'Pinned protection package')
    ctx=json.loads((bundle/'context.json').read_text());manifest=json.loads((bundle/'package.json').read_text())
    for n,h in manifest['files'].items():require(sha(bundle/n)==h,'Pinned package changed')
    stage=Path(tempfile.mkdtemp(prefix='copy.',dir=AREA));t=old.transport()
    names={'analysis.json','current-prefix.backup',*[f'p{n}-{k}.bin' for n in (2,3) for k in ['sb','gd','sector']]}
    for n in sorted(names):
        with (stage/n).open('xb') as out:
            r=subprocess.run(t.ssh(host)+[t.command(FETCH,result,n)],stdout=out,stderr=subprocess.PIPE,timeout=900)
            out.flush();os.fsync(out.fileno())
        require(r.returncode==0,'Current preimage transfer failed; no repair plan')
    report=json.loads((stage/'analysis.json').read_text());validate_report(report,ctx,manifest)
    require(sha(stage/'current-prefix.backup')==report['current_prefix_sha256'],'Independent current prefix copy')
    patches={}
    for n in (2,3):
        start,size=(128*1024*1024,512*1024*1024) if n==2 else (640*1024*1024,248561664*512)
        patch=metadata.sector_patch((stage/f'p{n}-sb.bin').read_bytes(),(stage/f'p{n}-gd.bin').read_bytes(),(stage/f'p{n}-sector.bin').read_bytes(),start,size)
        require(patch==report['patches'][str(n)],'Independent metadata capsule reconstruction');patches[str(n)]=patch
    after=old.expected_prefix(stage/'current-prefix.backup',patches['2'])
    write_new(stage/'context.json',(bundle/'context.json').read_bytes())
    plan={'schema':95,'current_prefix_before_sha256':report['current_prefix_sha256'],'current_prefix_after_sha256':after,
        'patches':patches,'native_receipt_sha256':sha(stage/'analysis.json'),'context_sha256':sha(stage/'context.json'),
        'independent_current_preimage_verified':True,'payload_write_authorized':False}
    write_new(stage/'repair-inputs.json',recovery.encoded(plan))
    survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    protection=t.native(host,"from pathlib import Path; import hashlib,json; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':[int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']]}))")
    require(protection['guard']==ctx['runtime_guard_sha256'] and protection['ro']==[1,1,1,1],'Final guard/RO missing')
    ack={'passed':True,'schema':95,'current_preimage_and_capsules_independently_verified':True,'no_payload_repair_executed':True,
        'all_aliases_RO_and_guard_verified':True,'remote_result':result,'package_manifest_sha256':p['manifest_sha256'],
        'files':{f.name:sha(f) for f in stage.iterdir()}}
    write_new(stage/'host-copy.json',recovery.encoded(ack));sync_dir(stage);(AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C95 guard/RO and independent current preimage verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','collect']);p.add_argument('--host',required=True)
    p.add_argument('--boot',type=int);p.add_argument('--result');a=p.parse_args()
    if a.action=='prepare':require(a.boot is not None,'Observed boot required');prepare(a.host,a.boot)
    else:require(a.result is not None,'Protected result required');collect(a.host,a.result)
