#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C86 pinned, finite capture packaging; deployment never starts sudo/helper."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,os,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_OFFSET
import phase4_root_recovery as recovery

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'physical-capture'
SCRIPTS=['phase4-physical-capture.py','phase4_backup_core.py','phase4_root_migration.py',
    'phase4-offline-backup.py','phase4_root_recovery.py','phase4_recovery_image.py']
def latest(folder,pointer):
    p=Path((folder/pointer).read_text().strip());require(p.resolve().is_relative_to(folder),'Private record location');return p
def transport():
    s=importlib.util.spec_from_file_location('transport',REPO/'port/scripts/run-phase4-offline-backup.py')
    t=importlib.util.module_from_spec(s);s.loader.exec_module(t);return t

def corrected_root(path,patch):
    offset=patch['sector_offset']-ROOT_OFFSET;replacement=bytes.fromhex(patch['after']);h=hashlib.sha256()
    require(0<=offset<512*1024*1024 and offset%512==0,'Patched root sector bounds')
    with path.open('rb') as f:
        position=0
        while data:=f.read(1024*1024):
            if position<=offset<position+len(data):
                p=offset-position;require(data[p:p+512].hex()==patch['before'],'C83 sector/backup binding')
                data=data[:p]+replacement+data[p+512:]
            h.update(data);position+=len(data)
    require(position==512*1024*1024,'C82 root image dimensions');return h.hexdigest()

def make_context(mode,host):
    for name in ['recovery-image','root-recovery','root-permissions','backup-native']:
        root=REPO/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Prior proof changed')
    prior=latest(WORK/'root-recovery','latest-readiness');meta=json.loads((prior/'analysis.json').read_text())
    require(meta['passed'] is True and sha(prior/'binding.json')==meta['private_binding_sha256'],'C84 source binding')
    binding=json.loads((prior/'binding.json').read_text());download=Path(binding['backup_download'])
    require(download.resolve().is_relative_to(WORK/'offline-backup'),'Backup location')
    ack=Path(binding['backup_host_copy']);require(sha(ack)==binding['backup_host_copy_sha256'],'Backup acknowledgment')
    receipt=json.loads((download/'backup.json').read_text());a=json.loads(ack.read_text())
    require(a['passed'] is True and a['independent_host_copy_verified'] is True and sha(download/'backup.json')==a['helper_receipt_sha256'],'Independent backup receipt')
    require(sha(download/'root.ext4')==receipt['artifacts']['root.ext4']['sha256'],'C82 root changed')
    complete=latest(WORK/'root-permissions','latest-complete');hostcopy=json.loads((complete/'host-copy.json').read_text())
    require(hostcopy['passed'] is True,'C83 host-copy')
    for n,h in hostcopy['files'].items():require(sha(complete/n)==h,'C83 copy changed')
    applied=json.loads((complete/'analysis.json').read_text());old=json.loads((complete/'context.json').read_text())
    require(applied['passed'] is True and applied['source_root_modes']=={'p2':0o755,'p3':0o755} and old['backup_receipt_sha256']==sha(download/'backup.json'),'C83 repair/source binding')
    t=transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import hashlib,json; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    require(live['guard']==applied['automount_guard_sha256'],'C83 runtime automount rule absent/changed')
    require(set(live['ro'].values())<=({1} if mode=='reference' else {0,1}),'Kernel RO preflight')
    context={'schema':86,'operation':mode,'mbr_sha256':old['mbr_sha256'],
        'boot_prefix_16MiB_sha256':old['boot_prefix_16MiB_sha256'],'automount_guard_sha256':live['guard'],
        'backup_private_files':binding['backup_private_files'],'backup_counter':receipt['boot_sequence'],
        'backup_prefix_sha256':receipt['prefix_sha256'],
        'reference_root_sha256':corrected_root(download/'root.ext4',applied['patches']['2'])}
    return context

def main(host,mode,journal=None,attempt_id=None,attempt_sha256=None):
    os.umask(0o077);AREA.mkdir(exist_ok=True);check=latest(AREA,'latest-checks');c=json.loads((check/'analysis.json').read_text())
    require(c['passed'] is True,'C86 checks required')
    for n,h in c['source_sha256'].items():require(sha(REPO/n)==h,'Tested source changed')
    context=make_context(mode,host);intent=None
    if mode=='postboot':
        require(journal is not None and attempt_id is not None and attempt_sha256 is not None,'Existing sealed handoff intent required; never create one here')
        require(journal.resolve().is_relative_to(WORK),'Private journal location')
        intent=recovery.load_attempt(journal,attempt_id,attempt_sha256)
        recovery.checked_attempt(intent,context['backup_private_files'],context['backup_counter'],context['backup_prefix_sha256'])
        context['attempt_sha256']=attempt_sha256
    else:require(journal is None and attempt_id is None and attempt_sha256 is None,'Reference cannot carry handoff intent')
    stage=Path(tempfile.mkdtemp(prefix='package-'+mode+'.',dir=AREA));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
    for n in SCRIPTS:write_new(bundle/n,(REPO/'port/scripts'/n).read_bytes())
    write_new(bundle/'context.json',(json.dumps(context,indent=2)+'\n').encode())
    if intent is not None:write_new(bundle/'attempt.json',recovery.encoded(intent))
    manifest={'operation':mode,'files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',(json.dumps(manifest,indent=2)+'\n').encode())
    target='/home/deck/muos-r35s-c86-'+mode+'-'+sha(bundle/'package.json')[:12];t=transport()
    original="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')","Path('"+target+"')").replace(original,repr(set(manifest['files'])|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    deployed=t.native(host,code,json.dumps({'files':files}).encode())
    require(deployed['passed'] is True and deployed['helper_started'] is False and deployed['files']=={n:v['sha256'] for n,v in files.items()},'Pinned deployment readback')
    result={'passed':True,'mode':mode,'target':target,'checks_sha256':sha(check/'analysis.json'),
        'source_sha256':c['source_sha256'],'deployment':deployed,'package_manifest_sha256':sha(bundle/'package.json')}
    write_new(stage/'analysis.json',(json.dumps(result,indent=2)+'\n').encode());(AREA/('latest-package-'+mode)).write_text(str(stage)+'\n')
    print('C86 package/deploy verified:',stage)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-physical-capture.py '+mode)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['reference','postboot']);p.add_argument('--host',required=True)
    p.add_argument('--journal',type=Path);p.add_argument('--attempt-id');p.add_argument('--attempt-sha256');a=p.parse_args()
    main(a.host,a.mode,a.journal,a.attempt_id,a.attempt_sha256)
