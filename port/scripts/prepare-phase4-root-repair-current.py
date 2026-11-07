#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C96 finite current-metadata package/collection; no host raw media access."""
from pathlib import Path
import argparse,base64,importlib,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums
import phase4_root_recovery as recovery

capture=importlib.import_module('prepare-phase4-card-rearm')
helper=importlib.import_module('phase4-root-repair-current')
REPO=capture.REPO;WORK=capture.WORK;AREA=WORK/'root-repair-current'

def current():
    stage=capture.initial.latest(capture.AREA,'latest-complete');ack=json.loads((stage/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['schema']==95 and ack['current_preimage_and_capsules_independently_verified'] is True
        and ack['all_aliases_RO_and_guard_verified'] is True and ack['no_payload_repair_executed'] is True,'Independent current preimages')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Current preimage/capsule changed')
    return stage

def prepare(host):
    os.umask(0o077);AREA.mkdir(exist_ok=True);stage=current()
    check=capture.initial.latest(AREA,'latest-checks');tests=json.loads((check/'analysis.json').read_text())
    require(tests['passed'] is True,'C96 current tests required')
    for n,h in tests['source_sha256'].items():require(sha(REPO/n)==h,'Tested current repair source changed')
    for name,h in tests['parent_proofs_sha256'].items():
        root=REPO/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent proof binding changed')
        for n,wanted in sums(root/'SHA256SUMS').items():require(sha(root/n)==wanted,'Parent proof changed')
    cap=json.loads((stage/'context.json').read_text());t=capture.old.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import hashlib,json,platform; print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(Path('/run/udev/rules.d/99-holo-automount.rules').read_bytes()).hexdigest(),'ro':[int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']]}))")
    qualified=json.loads((REPO/'dist/phase4/card-readiness/analysis.json').read_text())
    require(live['kernel']==qualified['kernel'] and live['guard']==cap['runtime_guard_sha256'] and live['ro']==[1,1,1,1],'Qualified kernel/RO/guard required')
    ctx={'schema':96,'operation':'repair-current-root-modes','capture_context_sha256':sha(stage/'context.json'),
        'native_capture_sha256':sha(stage/'analysis.json'),'host_current_ack_sha256':sha(stage/'host-copy.json'),
        'repair_inputs_sha256':sha(stage/'repair-inputs.json'),'qualified_kernel':live['kernel']}
    write_new(AREA/'package.claim',b'C96 package may be deployed; inspect before replacement\n');sync_dir(AREA)
    package=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));bundle=package/'bundle';bundle.mkdir(mode=0o700)
    documents={'context.json':None,'repair-inputs.json':stage/'repair-inputs.json','host-current-ack.json':stage/'host-copy.json',
        'native-capture.json':stage/'analysis.json','capture-context.json':stage/'context.json'}
    for n in helper.SOURCES-set(documents):write_new(bundle/n,(REPO/'port/scripts'/n).read_bytes())
    for n,path in documents.items():write_new(bundle/n,recovery.encoded(ctx) if path is None else path.read_bytes())
    helper.validate_lineage(bundle,ctx,importlib.import_module('phase4_backup_core'),recovery,capture.helper)
    manifest={'operation':'repair-current-root-modes','files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',recovery.encoded(manifest));target='/home/deck/muos-r35s-c96-repair-'+sha(bundle/'package.json')[:12]
    original="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')",'Path('+repr(target)+')').replace(original,repr(helper.SOURCES|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    result=t.native(host,code,json.dumps({'files':files}).encode())
    require(result['passed'] is True and result['helper_started'] is False and result['files']==manifest['files']|{'package.json':sha(bundle/'package.json')},'Finite deployment readback')
    write_new(package/'analysis.json',recovery.encoded({'passed':True,'target':target,'manifest_sha256':sha(bundle/'package.json'),
        'C95_current_preimage':str(stage),'checks_sha256':sha(check/'analysis.json'),'card_payload_written':False,'sudo_started':False}))
    sync_dir(package);(AREA/'latest-package').write_text(str(package)+'\n');sync_dir(AREA)
    print('C96 current metadata package verified:',package)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-root-repair-current.py repair')

def validate_report(r,ctx,plan,manifest):
    require(r['passed'] is True and type(r['schema']) is int and r['schema']==96 and r['operation']=='repair-current-root-modes','Native current repair')
    require(r['context_sha256']==recovery.hashed(recovery.encoded(ctx)) and r['source_sha256']==manifest['files'],'Current repair payload binding')
    require(r['prefix_before_sha256']==plan['current_prefix_before_sha256'] and r['prefix_after_sha256']==plan['current_prefix_after_sha256']
        and r['patches']==plan['patches'],'Current repair preimage/result binding')
    require(type(r['written_bytes']) is int and r['written_bytes']==1024 and type(r['written_sectors']) is int and r['written_sectors']==2 and
        r['root_modes']=={'p2':0o755,'p3':0o755} and r['p2_fsck_exit']==r['p3_fsck_exit']==0,'Fixed two-sector repair/fsck/modes')
    for n in ['all_four_aliases_kernel_readonly','userdata_before_and_after_matches_C82','full_prefix_posthash_verified',
        'no_superblock_or_GDT_changes','only_two_fixed_sectors_requested','cold_readback_verified']:require(r[n] is True,'Incomplete repair evidence')
    for n in ['seed_loaded_or_generated','automatic_retry_or_rollback','boot_handoff_authorized']:require(r[n] is False,'Unexpected repair side effect')

FETCH=r'''
from pathlib import Path
import os,re,stat,sys
root=Path(sys.argv[1]);name=sys.argv[2]
assert re.fullmatch(r'/var/tmp/muos-r35s-c96-repair\.[a-z0-9_]{8}',str(root))
assert name in {'analysis.json','unlock-intent.json','write-intent.json',*[f'p{n}-{k}.bin' for n in (2,3) for k in ['sb','gd','sector']]}
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd);assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400 and 0<s.st_size<=1024*1024
 raw=os.read(fd,s.st_size+1);a=os.fstat(fd);assert len(raw)==s.st_size and (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)
 sys.stdout.buffer.write(raw)
finally:os.close(fd)
'''

def collect(host,result):
    os.umask(0o077);require(re.fullmatch(r'/var/tmp/muos-r35s-c96-repair\.[a-z0-9_]{8}',result),'Finite repair result path')
    package=capture.initial.latest(AREA,'latest-package');p=json.loads((package/'analysis.json').read_text());bundle=package/'bundle'
    require(p['passed'] is True and sha(bundle/'package.json')==p['manifest_sha256'],'Pinned repair package')
    ctx=json.loads((bundle/'context.json').read_text());manifest=json.loads((bundle/'package.json').read_text())
    for n,h in manifest['files'].items():require(sha(bundle/n)==h,'Repair package changed')
    cap,plan=helper.validate_lineage(bundle,ctx,importlib.import_module('phase4_backup_core'),recovery,capture.helper)
    stage=Path(tempfile.mkdtemp(prefix='copy.',dir=AREA));t=capture.old.transport()
    names={'analysis.json','unlock-intent.json','write-intent.json',*[f'p{n}-{k}.bin' for n in (2,3) for k in ['sb','gd','sector']]}
    for n in sorted(names):
        with (stage/n).open('xb') as out:
            r=subprocess.run(t.ssh(host)+[t.command(FETCH,result,n)],stdout=out,stderr=subprocess.PIPE,timeout=60)
            out.flush();os.fsync(out.fileno())
        require(r.returncode==0,'Repair evidence transfer failed')
    report=json.loads((stage/'analysis.json').read_text());validate_report(report,ctx,plan,manifest)
    require(report['boot_sequence']==cap['expected_boot_sequence'] and report['runtime_guard_sha256']==cap['runtime_guard_sha256'],'Counter/guard binding')
    journal=[json.loads((stage/n).read_text()) for n in ['unlock-intent.json','write-intent.json']]
    expected_sectors={n:{'offset':v['sector_offset'],'before_sha256':v['before_sha256'],'after_sha256':v['after_sha256']} for n,v in plan['patches'].items()}
    for j in journal:
        require(j['kind']=='CURRENT_ROOT_MODE_REPAIR_MAY_HAVE_STARTED' and j['context_sha256']==sha(bundle/'context.json') and
            j['current_prefix_before_sha256']==plan['current_prefix_before_sha256'] and j['sectors']==expected_sectors and
            j['automatic_retry_or_rollback'] is False,'Durable current-sector journal binding')
    original=Path(p['C95_current_preimage']);require(original.resolve().is_relative_to(capture.AREA),'Known C95 preimage')
    for n in names-{'analysis.json','unlock-intent.json','write-intent.json'}:require(sha(stage/n)==sha(original/n),'Pre-repair capsule changed')
    survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import hashlib,json,platform; print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(Path('/run/udev/rules.d/99-holo-automount.rules').read_bytes()).hexdigest(),'ro':[int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']]}))")
    require(live['kernel']==ctx['qualified_kernel'] and live['guard']==cap['runtime_guard_sha256'] and live['ro']==[1,1,1,1],'Final guard/RO/kernel')
    ack={'passed':True,'schema':96,'current_two_sector_repair_independently_verified':True,'all_aliases_RO_and_guard_verified':True,
        'current_prefix_after_sha256':plan['current_prefix_after_sha256'],'package_manifest_sha256':p['manifest_sha256'],
        'files':{f.name:sha(f) for f in stage.iterdir()}}
    write_new(stage/'host-copy.json',recovery.encoded(ack));sync_dir(stage);(AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C96 current repair and independent evidence verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','collect']);p.add_argument('--host',required=True);p.add_argument('--result');a=p.parse_args()
    if a.action=='prepare':prepare(a.host)
    else:require(a.result is not None,'Repair result required');collect(a.host,a.result)
