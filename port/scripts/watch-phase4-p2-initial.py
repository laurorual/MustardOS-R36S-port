#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Observe an already-running C94 operation; never start/stop/retry the writer."""
from pathlib import Path
import argparse,importlib,json,os,re,subprocess,sys,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require

prep=importlib.import_module('prepare-phase4-p2-initial')
monitor=importlib.import_module('watch-phase4-p2-recovery')
STATUS=monitor.STATUS.replace('muos-r35s-c89-recovery','muos-r35s-c94-initial').replace('muos-r35s-c89-failure','muos-r35s-c94-failure')

def claim(area):
    write_new(area/'watch-initial.claim',b'C94 collection may have started; inspect before replacement\n');sync_dir(area)

def main(host,result,helper):
    os.umask(0o077)
    require(re.fullmatch(r'/var/tmp/muos-r35s-c94-initial\.[a-z0-9_]{8}',result) and
        re.fullmatch(r'muos-r35s-c94\.[a-z0-9_]{8}',helper),'Finite existing initial attempt')
    require(not (prep.AREA/'latest-complete').exists(),'Collected attempt already exists')
    tests=prep.initial.latest(prep.AREA,'latest-transport-checks');checks=json.loads((tests/'analysis.json').read_text())
    require(checks['passed'] is True,'Tested observer required')
    for n,h in checks['source_sha256'].items():require(sha(prep.REPO/n)==h,'Tested observer changed')
    package=prep.initial.latest(prep.AREA,'latest-package');bundle=package/'bundle'
    record=json.loads((package/'analysis.json').read_text())
    require(record['passed'] is True and sha(bundle/'package.json')==record['package_manifest_sha256'],'Pinned package')
    manifest=json.loads((bundle/'package.json').read_text());ctx=json.loads((bundle/'context.json').read_text())
    for n,h in manifest['files'].items():
        require(sha(bundle/n)==h,'Observed package changed')
        if n.endswith('.py'):require(sha(prep.REPO/'port/scripts'/n)==h,'Observed source changed')
    claim(prep.AREA);stage=Path(tempfile.mkdtemp(prefix='watch.',dir=prep.AREA))
    write_new(stage/'request.json',json.dumps({'host':host,'result':result,'helper':helper,'package':str(package),
        'package_manifest_sha256':record['package_manifest_sha256'],'observer_source_sha256':sha(Path(__file__))}).encode())
    (prep.AREA/'latest-watch').write_text(str(stage)+'\n');sync_dir(prep.AREA)
    t=prep.initial.legacy.prep.prep.transport()
    def run(label,argv):
        with (stage/(label+'.stdout')).open('xb') as out,(stage/(label+'.stderr')).open('xb') as err:
            result=subprocess.run(argv,stdout=out,stderr=err,timeout=900)
            out.flush();os.fsync(out.fileno());err.flush();os.fsync(err.fileno())
        write_new(stage/(label+'.exit'),(str(result.returncode)+'\n').encode())
        require(result.returncode==0,'Collection/proof failed; preserve partials without retry')
    try:
        monitor.observe(stage,lambda:t.native(host,STATUS,json.dumps({'result':result}).encode()),
            lambda:run('collect',[sys.executable,str(prep.REPO/'port/scripts/collect-phase4-p2-initial.py'),'--host',host,'--result',result]),
            lambda:run('proof',[sys.executable,str(prep.REPO/'port/scripts/package-phase4-p2-initial-native.py')]),helper,ctx)
    except BaseException as error:
        write_new(stage/'failure.json',json.dumps({'passed':False,'error_type':type(error).__name__,'reason':str(error),
            'writer_started_stopped_or_retried':False,'card_must_stay_offline':True}).encode());sync_dir(stage);raise
    print('C94 OBSERVER COMPLETE '+str(stage),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True)
    p.add_argument('--result',required=True);p.add_argument('--root-helper',required=True)
    a=p.parse_args();main(a.host,a.result,a.root_helper)
