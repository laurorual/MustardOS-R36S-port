#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Observe one already-running C89 attempt and collect it once, without sudo.

Never starts/stops/retries a card writer. A timeout or SSH failure only stops
this observer; the Deck operation and its partial journal remain untouched.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,os,re,stat,subprocess,sys,tempfile,time
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require,DECK_CID,CAPACITY

STATUS=r'''
from pathlib import Path
import hashlib,json,os,platform,re,stat,sys,time
r=json.load(sys.stdin);p=Path(r['result'])
assert re.fullmatch(r'/var/tmp/muos-r35s-c89-recovery\.[a-z0-9_]{8}',str(p))
s=p.lstat();assert stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700
card=Path('/sys/class/block/mmcblk0');v=list(map(int,(card/'stat').read_text().split()))
rule=Path('/run/udev/rules.d/99-holo-automount.rules')
print(json.dumps({'time':time.time(),'read_bytes':v[2]*512,'write_bytes':v[6]*512,
 'cid_sha256':hashlib.sha256((card/'device/cid').read_text().strip().lower().encode()).hexdigest(),
 'capacity_sectors':int((card/'size').read_text()),'kernel':platform.release(),
 'guard_sha256':hashlib.sha256(rule.read_bytes()).hexdigest(),
 'ro':[int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']],
 'root_helpers':sorted(p.name for p in Path('/run').glob('muos-r35s-c*')),
 'owned_complete':s.st_uid==os.getuid() and (p/'analysis.json').is_file(),
 'failures':sorted(p.name for p in Path('/var/tmp').glob('muos-r35s-c89-failure.*') if p.stat().st_uid==os.getuid())}))
'''

def state_action(value,helper,context):
    require(value['cid_sha256']==DECK_CID and value['capacity_sectors']==CAPACITY,
        'Observer card identity changed; no collection')
    require(value['kernel']==context['qualified_kernel'] and
        value['guard_sha256']==context['physical_capture']['automount_guard_sha256'],
        'Observer kernel/guard changed; no collection')
    require(value['ro'] in ([1,1,1,1],[0,1,0,1]),'Unexpected protection state; inspect, do not retry writer')
    require(not value['failures'],'Recovery failure report exists; preserve partials, no automatic retry')
    if value['owned_complete']:
        require(value['root_helpers']==[] and value['ro']==[1,1,1,1],
            'Completion still has a helper or writable alias; do not collect yet')
        return 'collect'
    require(value['root_helpers']==[helper],'Expected running helper disappeared/changed; inspect partial attempt')
    return 'wait'

def claim_observer(area):
    # Exclusive persistent claim also covers concurrent starts and interruption
    # before the latest-pointer is published. Never silently resume a collector.
    write_new(area/'watch-recover.claim',b'C89 observer may have collected; inspect before any replacement\n')
    sync_dir(area)

def observe(stage,poll,collect,package,helper,context,seconds=21600,interval=30,
            now=time.monotonic,sleep=time.sleep):
    require(0<seconds<=21600 and 0<interval<=60,'Bounded observer duration/interval')
    start=now();index=0
    while True:
        require(now()-start<=seconds,'Observer timeout; Deck writer was not interrupted, keep card offline')
        value=poll();action=state_action(value,helper,context)
        write_new(stage/f'status-{index:04d}.json',(json.dumps(value,indent=2)+'\n').encode())
        sync_dir(stage);index+=1
        print(json.dumps({'observation':index,'action':action,'read_GiB':round(value['read_bytes']/1024**3,2),
            'written_MiB':round(value['write_bytes']/1024**2,2)}),flush=True)
        if action=='collect':
            # Exactly one invocation. Failure stops here; never retry a writer
            # or even a partial collection automatically.
            collect();package()
            write_new(stage/'complete.json',b'{"passed":true,"writer_started_or_retried":false,"collection_and_proof_complete":true}\n')
            sync_dir(stage);return
        sleep(interval)

def main(host,result,helper):
    os.umask(0o077)
    require(re.fullmatch(r'/var/tmp/muos-r35s-c89-recovery\.[a-z0-9_]{8}',result) and
        re.fullmatch(r'muos-r35s-c89\.[a-z0-9_]{8}',helper),'Finite existing recovery attempt required')
    prep=importlib.import_module('prepare-phase4-p2-recovery');area=prep.AREA
    require(not (area/'latest-complete-recover').exists(),'A collected attempt already exists; inspect it instead')
    tested=prep.prep.prep.latest(area,'latest-watch-checks')
    checks=json.loads((tested/'analysis.json').read_text())
    require(checks['passed'] is True,'Observer checks required')
    for name,h in checks['source_sha256'].items():require(sha(prep.REPO/name)==h,'Tested observer source changed')
    package=prep.prep.prep.latest(area,'latest-package-recover')
    report=json.loads((package/'analysis.json').read_text());bundle=package/'bundle'
    require(report['passed'] is True and sha(bundle/'package.json')==report['package_manifest_sha256'],'Pinned package')
    manifest=json.loads((bundle/'package.json').read_text());context=json.loads((bundle/'context.json').read_text())
    for name,h in manifest['files'].items():
        require(sha(bundle/name)==h,'Observed package changed')
        if name.endswith('.py'):require(sha(prep.REPO/'port/scripts'/name)==h,'Observed source changed')
    claim_observer(area)
    stage=Path(tempfile.mkdtemp(prefix='watch-recover.',dir=area))
    write_new(stage/'request.json',(json.dumps({'host':host,'result':result,'helper':helper,
        'package':str(package),'package_manifest_sha256':report['package_manifest_sha256'],
        'observer_source_sha256':sha(Path(__file__))},indent=2)+'\n').encode())
    (area/'latest-watch-recover').write_text(str(stage)+'\n');sync_dir(area)
    t=prep.prep.prep.transport()
    def run(label,argv):
        with (stage/(label+'.stdout')).open('xb') as out,(stage/(label+'.stderr')).open('xb') as err:
            r=subprocess.run(argv,stdout=out,stderr=err,timeout=900)
            out.flush();os.fsync(out.fileno());err.flush();os.fsync(err.fileno())
        write_new(stage/(label+'.exit'),(str(r.returncode)+'\n').encode())
        require(r.returncode==0,'Observer '+label+' failed; preserve partials, no automatic retry')
    try:
        observe(stage,lambda:t.native(host,STATUS,json.dumps({'result':result}).encode()),
            lambda:run('collect',[sys.executable,str(prep.REPO/'port/scripts/collect-phase4-p2-recovery.py'),
                '--host',host,'--result',result]),
            lambda:run('proof',[sys.executable,str(prep.REPO/'port/scripts/package-phase4-p2-recovery-native.py')]),
            helper,context)
    except BaseException as error:
        write_new(stage/'failure.json',(json.dumps({'passed':False,'error_type':type(error).__name__,
            'reason':str(error),'writer_started_stopped_or_retried':False,'card_must_stay_offline':True},indent=2)+'\n').encode())
        sync_dir(stage);raise
    print('C89 OBSERVER COMPLETE '+str(stage),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True)
    p.add_argument('--result',required=True);p.add_argument('--root-helper',required=True)
    a=p.parse_args();main(a.host,a.result,a.root_helper)
