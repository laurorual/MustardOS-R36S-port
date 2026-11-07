#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C102 finite additive layout update on the already qualified C79 boot.

prepare reads only; apply dispatches once; collect never dispatches or retries.
Private stages retain boot identities, foundation hashes and authentic receipts.
"""
from pathlib import Path
import argparse,importlib,ipaddress,json,os,re,subprocess,tarfile,tempfile,time
from phase4_candidate import sha,sums
from phase4_backup_core import sync_dir
import phase4_c79_session as session
import phase4_c79_layout as layout
from phase4_gambatte_install import INFRA

REPO=session.REPO;WORK=session.WORK;AREA=WORK/'c79-layout-install'
NATIVE=REPO/'port/device/rk-r35s-p0/c79-layout-install'

def write(path,value):
    data=value.encode() if isinstance(value,str) else value
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())

def encoded(value):return json.dumps(value,indent=2)+'\n'

def inputs():
    parents={}
    for name in ['c79-layout','c79-session','initial-boot-native']:
        root=REPO/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():assert sha(root/n)==h,(name,n)
        parents[name]=sha(root/'SHA256SUMS')
    public=json.loads((REPO/'dist/phase4/c79-layout/analysis.json').read_text())
    assert public['passed'] is True and public['schema']==100 and public['source_factory_sha256']==layout.C79_SHA
    assert public['added_paths']==['etc/asound.conf','mnt/mmc'] and public['new_regular_file_payload_bytes']==444
    checks=json.loads((REPO/'dist/phase4/c79-layout/checks.json').read_text())
    assert checks['passed'] and checks['case_count']==29
    for n,h in checks['source_sha256'].items():assert sha(REPO/n)==h,n
    qualified,boot=session.qualified()
    common=session.legacy.current_common('',boot['boot_sequence'],boot['boot_sequence'])
    collector=importlib.import_module('collect-phase4-initial-boot')
    composition=Path((WORK/'initial-migration/latest-complete').read_text().strip())
    assert composition.resolve().is_relative_to(WORK/'initial-migration')
    common,matching=collector.matched_common(common,json.loads((composition/'tree.json').read_text()))
    assert matching['guard_file_count']==141
    common+='[ "$(cat /proc/sys/kernel/random/boot_id)" = '+boot['kernel_boot_id']+' ]\n'
    common+='''[ ! -e /var/lib/muos-diagnostic/c25.once ];[ ! -L /var/lib/muos-diagnostic/c25.once ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
'''
    common+=f'''[ ! -L /{layout.TEMPLATE} ];[ "$(stat -c '%u:%g:%a:%h:%s' /{layout.TEMPLATE})" = 0:0:755:1:444 ]
printf '%s  %s\\n' {layout.TEMPLATE_SHA} /{layout.TEMPLATE} | sha256sum -c - >/dev/null
'''
    foundation=re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",common)
    assert len(foundation)==142 and len(set(n for _,n in foundation))==142
    return common,foundation,boot,parents,sha(qualified/'analysis.json')

ABSENT='''
for p in /etc /mnt;do [ ! -L "$p" ];[ "$(stat -c '%u:%g:%a' "$p")" = 0:0:755 ];done
for p in /etc/asound.conf /etc/asound.conf.c102-new /mnt/mmc;do [ ! -e "$p" ];[ ! -L "$p" ];done
[ "$(stat -c %h /mnt)" = 2 ]
[ -z "$(find /mnt -mindepth 1 -maxdepth 1 -print)" ]
'''
HEALTH=f'''
[ ! -L /etc ];[ "$(stat -c '%u:%g:%a' /etc)" = 0:0:755 ]
[ ! -L /etc/asound.conf ];[ -f /etc/asound.conf ]
[ "$(stat -c '%u:%g:%a:%h:%s' /etc/asound.conf)" = 0:0:644:1:444 ]
printf '%s  %s\\n' {layout.TEMPLATE_SHA} /etc/asound.conf | sha256sum -c - >/dev/null
[ ! -e /etc/asound.conf.c102-new ];[ ! -L /etc/asound.conf.c102-new ]
[ ! -L /mnt ];[ "$(stat -c '%u:%g:%a:%h' /mnt)" = 0:0:755:3 ]
[ ! -L /mnt/mmc ];[ -d /mnt/mmc ];[ "$(stat -c '%u:%g:%a:%h' /mnt/mmc)" = 0:0:755:2 ]
[ -z "$(find /mnt/mmc -mindepth 1 -maxdepth 1 -print)" ]
[ "$(find /mnt -mindepth 1 -maxdepth 1 -print)" = /mnt/mmc ]
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['prepare','apply','collect'])
    p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--stage',type=Path)
    args=p.parse_args();os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
    common,foundation,boot,parents,boot_sha=inputs()
    check=importlib.import_module('check-phase4-c79-layout-install')
    source_sha={str(n.relative_to(REPO)):sha(n) for n in check.sources()}
    tests=Path((AREA/'latest-checks').read_text().strip())
    assert tests.resolve().is_relative_to(AREA)
    tested=json.loads((tests/'analysis.json').read_text())
    assert tested['passed'] and tested['case_count']==35 and tested['source_sha256']==source_sha
    stage=Path(tempfile.mkdtemp(prefix='install.',dir=AREA)) if args.operation=='prepare' else (
        args.stage.resolve() if args.stage else Path((AREA/'latest-plan').read_text().strip()))
    assert stage.resolve().is_relative_to(AREA) and not stage.is_symlink()
    ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes',
        '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
        '-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+str(args.host)]
    def remote(label,code,timeout=90):
        # Never overwrite a receipt on interrupted collection or redispatch.
        suffix=label
        if (stage/(suffix+'.sh')).exists():suffix=label+'.'+str(time.time_ns())
        write(stage/(suffix+'.sh'),code)
        r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
        for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write(stage/(suffix+'.'+ext),v)
        assert r.returncode==0,('C102 remote step failed; preserve stage, do not reapply',stage,suffix)
        return r.stdout
    if args.operation=='prepare':
        remote('survey',common+ABSENT+INFRA)
        payload=stage/'payload';payload.mkdir(mode=0o700)
        template=WORK/'gambatte-image/image.zal39n7u/target'/layout.TEMPLATE
        assert sha(template)==layout.TEMPLATE_SHA and template.stat().st_size==444
        write(payload/'asound.conf',template.read_bytes());(payload/'asound.conf').chmod(0o644)
        write(payload/'foundation.sha256',''.join(h+'  '+n+'\n' for h,n in sorted(foundation)))
        write(stage/'guard.sh',common)
        for name in ['transaction.sh','native.sh']:write(stage/name,(NATIVE/name).read_bytes())
        plan={'schema':102,'experiment':'C102_ADDITIVE_C79_LAYOUT','boot_sequence':boot['boot_sequence'],
            'new_file':{'path':'etc/asound.conf','bytes':444,'mode':0o644,'sha256':layout.TEMPLATE_SHA},
            'new_directory':{'path':'mnt/mmc','mode':0o755,'empty':True},
            'before':'both absent; empty /mnt; no staging path','existing_files_replaced':0,
            'foundation_files':141,'template_also_guarded':True,'parent_proofs_sha256':parents,
            'C97_analysis_sha256':boot_sha,'checks_sha256':sha(tests/'analysis.json'),'source_sha256':source_sha,
            'rootfs_raw_reflash_seed_counter_or_user_data_write':False,'activation':'none'}
        write(stage/'plan.json',encoded(plan))
        write(stage/'absence-backup.json',encoded({'schema':102,'plan_sha256':sha(stage/'plan.json'),
            'paths_absent':['etc/asound.conf','etc/asound.conf.c102-new','mnt/mmc'],
            'restore':'matching owned file only; empty owned directory only; unknown partials retained',
            'private_bytes_backed_up':False,'independent_existing_C82_backup_retained':True}))
        files=[stage/n for n in ['guard.sh','native.sh','transaction.sh']]+sorted(payload.iterdir())
        write(stage/'SHA256SUMS',''.join(sha(q)+'  '+str(q.relative_to(stage))+'\n' for q in files))
        with tarfile.open(stage/'deployment.tar','x') as tar:
            for q in files+[stage/'SHA256SUMS']:
                info=tar.gettarinfo(str(q),arcname=str(q.relative_to(stage)));info.uid=info.gid=0
                info.uname=info.gname='root'
                assert info.isfile() and not q.is_symlink()
                with q.open('rb') as stream:tar.addfile(info,stream)
        write(stage/'manifest.json',encoded({'plan_sha256':sha(stage/'plan.json'),
            'absence_backup_sha256':sha(stage/'absence-backup.json'),'deployment_sha256':sha(stage/'deployment.tar'),
            'guard_sha256':sha(stage/'guard.sh'),'host':str(args.host),'kernel_boot_id':boot['kernel_boot_id']}))
        with (stage/'deployment.tar').open('rb') as stream:os.fsync(stream.fileno())
        sync_dir(payload);sync_dir(stage)
        (AREA/'latest-plan').write_text(str(stage)+'\n');sync_dir(AREA)
        print('C102 absence plan and public payload synced; device read-only:',stage);return
    plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
    assert meta['host']==str(args.host) and meta['kernel_boot_id']==boot['kernel_boot_id']
    assert plan['source_sha256']==source_sha and plan['parent_proofs_sha256']==parents
    assert plan['checks_sha256']==sha(tests/'analysis.json') and plan['C97_analysis_sha256']==boot_sha
    for n,key in [('plan.json','plan_sha256'),('absence-backup.json','absence_backup_sha256'),
        ('deployment.tar','deployment_sha256'),('guard.sh','guard_sha256')]:assert sha(stage/n)==meta[key],n
    assert (stage/'guard.sh').read_text()==common
    if args.operation=='apply':
        assert not (stage/'dispatch.claim').exists(),'Never redispatch an existing attempt; collect it'
        remote('before',common+ABSENT+INFRA)
        write(stage/'dispatch.claim','C102 attempt started; collect or inspect, never redispatch\n');sync_dir(stage)
        directory=remote('allocate',common+'mktemp -d /run/muos-c102.XXXXXX\n').strip()
        assert re.fullmatch('/run/muos-c102[.][A-Za-z0-9]{6}',directory)
        write(stage/'remote-directory',directory+'\n');sync_dir(stage)
        r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=30)
        assert r.returncode==0,('Payload transfer failed; inspect existing capsule',stage)
        remote('unpack',f'''set -eu
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c - >/dev/null
tar -xf {directory}/deployment.tar -C {directory}
cd {directory};sha256sum -c SHA256SUMS >/dev/null
''')
        remote('inspect',common+f'sh {directory}/native.sh {directory} inspect\n')
        remote('mounts-before',common+f'cat /proc/1/mountinfo > {directory}/mounts.before\n')
        remote('dispatch',common+f'''nohup setsid sh {directory}/native.sh {directory} apply > {directory}/apply.log 2>&1 < /dev/null &
echo C102_DISPATCHED
''')
    else:
        directory=(stage/'remote-directory').read_text().strip()
        assert re.fullmatch('/run/muos-c102[.][A-Za-z0-9]{6}',directory)
    if (stage/'analysis.json').exists():raise AssertionError('C102 already collected; never repeat a completed increment')
    for _ in range(20):
        r=subprocess.run(ssh+['test -f '+directory+'/apply.done'],capture_output=True,timeout=12)
        if r.returncode==0:break
        time.sleep(1)
    else:raise AssertionError('C102 pending; collect existing attempt, do not redispatch')
    result=remote('result',f'set -eu\ncat {directory}/apply.result\ncat {directory}/apply.log\n')
    assert result.splitlines()[0]=='0' and 'C102_INSTALLED_444_BYTES_ONE_DIRECTORY_ROOT_RO' in result,(
        'C102 failed: inspect retained capsule and rollback log, never reapply',stage)
    health=common+HEALTH
    assert remote('after',health+INFRA)==(stage/'before.stdout').read_text(),'Infrastructure changed'
    remote('mounts-private',health+f'''cmp /proc/1/mountinfo {directory}/mounts.before
cmp {directory}/private.before {directory}/private.after
''')
    # The raw private fingerprint stays in the root-owned RAM capsule only.
    write(stage/'collected-result.txt',result)
    remote('cleanup',health+f'''[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
! findmnt -rn -M {directory} >/dev/null
cmp /proc/1/mountinfo {directory}/mounts.before
rm -rf {directory}
[ ! -e {directory} ]
echo C102_RAM_REMOVED_ROOT_RO
''')
    assert remote('post-cleanup-health',health+INFRA)==(stage/'before.stdout').read_text()
    report={'passed':True,'schema':102,'experiment':'C102_INSTALLED_C79_LAYOUT','boot_sequence':plan['boot_sequence'],
        'plan_sha256':sha(stage/'plan.json'),'checks_sha256':plan['checks_sha256'],
        'source_sha256':source_sha,'parent_proofs_sha256':parents,
        'public_file_added_bytes':444,'empty_directory_added':1,'existing_files_replaced':0,
        'foundation_files_reverified':141,'public_template_unchanged':True,'root_read_only':True,
        'private_state_fingerprint_matched':True,'infrastructure_and_global_mounts_preserved':True,
        'p1_or_p3_mounted':False,'seed_counter_or_user_data_updated':False,'reboot_or_UI_started':False,
        'RAM_capsule_removed':True,'native_layout_runtime_or_new_boot_qualified':False}
    write(stage/'analysis.json',encoded(report));sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C102 installed: 444 bytes and one empty directory; root RO, private state preserved:',stage)

if __name__=='__main__':main()
