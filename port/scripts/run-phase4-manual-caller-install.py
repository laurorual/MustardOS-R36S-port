#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C105 finite additive caller install, no startup change or graphical test."""
import argparse,ipaddress,json,os,re,subprocess,tarfile,tempfile,time
from phase4_manual_caller import *
from phase4_backup_core import write_new,sync_dir
from phase4_gambatte_install import INFRA

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['prepare','apply','collect'])
    p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--stage',type=Path);a=p.parse_args()
    os.umask(0o077);package=Path((AREA/'latest-package').read_text().strip())
    require(package.resolve().is_relative_to(AREA),'Known C105 package')
    report=json.loads((package/'analysis.json').read_text())
    for n,h in report['source_sha256'].items():require(sha(REPO/n)==h,'Package source changed')
    for n,h in report['package_files'].items():require(sha(package/'target'/PREFIX/n)==h,'Package changed')
    for n,h in report['adapter_sha256'].items():require(sha(package/n)==h,'Native adapter changed')
    checks=Path((AREA/'latest-checks').read_text().strip());require(checks.resolve().is_relative_to(AREA),'Known checks')
    tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True and tested['package_analysis_sha256']==sha(package/'analysis.json') and
        tested['source_sha256']==report['source_sha256'],'Tested package and install scope required')
    prior,boot=qualified();guard=common()
    stage=Path(tempfile.mkdtemp(prefix='install.',dir=AREA)) if a.operation=='prepare' else (
        a.stage.resolve() if a.stage else Path((AREA/'latest-plan').read_text().strip()))
    require(stage.resolve().is_relative_to(AREA),'Known installation stage')
    ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
        '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),
        '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
    def write(name,data):write_new(stage/name,data.encode() if isinstance(data,str) else data)
    def remote(label,code,timeout=120):
        if (stage/(label+'.sh')).exists():label+='.'+str(time.time_ns())
        write(label+'.sh',code)
        r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
        for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write(label+'.'+n,v)
        require(r.returncode==0,'C105 failed '+label+'; inspect existing attempt: '+str(stage))
        return r.stdout
    absent=f'''[ ! -e /{PREFIX} ];[ ! -L /{PREFIX} ]
[ ! -e /{PREFIX}.c105-new ];[ ! -L /{PREFIX}.c105-new ]
'''
    health=''
    for n,h in report['package_files'].items():
        health+=f'''[ -f /{PREFIX}/{n} ];[ ! -L /{PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{PREFIX}/{n} | sha256sum -c - >/dev/null
'''
    health+=f'''[ ! -L /{PREFIX} ];[ "$(stat -c '%u:%g:%a' /{PREFIX})" = 0:0:755 ]
[ "$(find /{PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 17 ]
'''
    if a.operation=='prepare':
        remote('survey',guard+absent+INFRA)
        payload=stage/'payload';(payload/'new'/PREFIX).mkdir(mode=0o700,parents=True)
        for n in NAMES:
            write_new(payload/'new'/PREFIX/n,(package/'target'/PREFIX/n).read_bytes());(payload/'new'/PREFIX/n).chmod(0o644)
        write_new(payload/'FILES',''.join(report['package_files'][n]+' 644 '+PREFIX+'/'+n+'\n' for n in NAMES).encode())
        rows=re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",guard)
        require(len(rows)==143,'C104 foundation plus layout guards')
        write_new(payload/'foundation.sha256',''.join(h+'  '+n+'\n' for h,n in rows).encode())
        write_new(payload/'boot-seq',(str(boot['boot_sequence'])+'\n').encode());write_new(payload/'boot-uuid',(boot['kernel_boot_id']+'\n').encode())
        for n in ['native.sh','transaction.sh']:write(n,(package/n).read_bytes())
        write('guard.sh',guard)
        plan={'schema':105,'boot_sequence':boot['boot_sequence'],'prefix':PREFIX,'absent_owned_roots':[PREFIX],
            'files':report['package_files'],'bytes':report['bytes'],'existing_files_replaced':0,
            'activation':'manual only','source_sha256':report['source_sha256'],
            'package_analysis_sha256':sha(package/'analysis.json'),'checks_sha256':sha(checks/'analysis.json'),
            'C104_analysis_sha256':sha(prior/'analysis.json'),'parent_proofs_sha256':report['parent_proofs_sha256']}
        write('plan.json',json.dumps(plan,indent=2)+'\n')
        write('absence-backup.json',json.dumps({'schema':105,'plan_sha256':sha(stage/'plan.json'),
            'prefix_absent':PREFIX,'restore':'only reviewed matching leaves and owned empty directory',
            'private_bytes_copied':False,'C82_independent_backup_retained':True},indent=2)+'\n')
        files=sorted(p for p in payload.rglob('*') if p.is_file())+[stage/n for n in ['native.sh','transaction.sh','guard.sh']]
        write('SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(stage))+'\n' for p in files))
        with tarfile.open(stage/'deployment.tar','x') as tar:
            for q in files+[stage/'SHA256SUMS']:
                info=tar.gettarinfo(str(q),arcname=str(q.relative_to(stage)));info.uid=info.gid=0;info.uname=info.gname='root'
                require(info.isfile() and not q.is_symlink(),'Only regular deployment files')
                with q.open('rb') as stream:tar.addfile(info,stream)
        write('manifest.json',json.dumps({'host':str(a.host),'kernel_boot_id':boot['kernel_boot_id'],
            'files':{n:sha(stage/n) for n in ['plan.json','absence-backup.json','deployment.tar','guard.sh']}},indent=2)+'\n')
        with (stage/'deployment.tar').open('rb') as stream:os.fsync(stream.fileno())
        sync_dir(stage);(AREA/'latest-plan').write_text(str(stage)+'\n');sync_dir(AREA)
        print('C105 exact caller absence plan synced; no persistent write:',stage);return
    plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
    require(meta['host']==str(a.host) and meta['kernel_boot_id']==boot['kernel_boot_id'] and
        plan['package_analysis_sha256']==sha(package/'analysis.json') and plan['checks_sha256']==sha(checks/'analysis.json'),
        'Installation binding changed')
    for n,h in meta['files'].items():require(sha(stage/n)==h,'Plan/absence/deployment changed')
    require((stage/'guard.sh').read_text()==guard,'Exact qualified boot guard')
    if a.operation=='apply':
        require(not (stage/'dispatch.claim').exists(),'Never redispatch; collect or inspect existing attempt')
        remote('before',guard+absent+INFRA)
        write('dispatch.claim','C105 one attempt; never redispatch after interruption\n');sync_dir(stage)
        directory=remote('allocate',guard+'mktemp -d /run/muos-c105.XXXXXX\n').strip()
        require(re.fullmatch('/run/muos-c105[.][A-Za-z0-9]{6}',directory),'Finite RAM capsule')
        write('remote-directory',directory+'\n');sync_dir(stage)
        r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=30)
        require(r.returncode==0,'Transfer failed; inspect existing capsule')
        remote('unpack',f'''set -eu
printf '%s  %s\\n' {meta['files']['deployment.tar']} {directory}/deployment.tar | sha256sum -c - >/dev/null
tar -xf {directory}/deployment.tar -C {directory}
cd {directory};sha256sum -c SHA256SUMS >/dev/null
''')
        remote('inspect',guard+f'sh {directory}/native.sh {directory} inspect\n')
        remote('mounts-before',guard+f'cat /proc/1/mountinfo > {directory}/mounts.before\n')
        remote('dispatch',guard+f'''nohup setsid sh {directory}/native.sh {directory} apply > {directory}/apply.log 2>&1 < /dev/null &
echo C105_DISPATCHED
''')
    else:
        directory=(stage/'remote-directory').read_text().strip()
        require(re.fullmatch('/run/muos-c105[.][A-Za-z0-9]{6}',directory),'Known RAM capsule')
    for _ in range(120):
        r=subprocess.run(ssh+['test -f '+directory+'/apply.done'],capture_output=True,timeout=10)
        if r.returncode==0:break
        time.sleep(1)
    else:raise ValueError('C105 pending: collect existing attempt, never redispatch')
    result=remote('result',f'set -eu\ncat {directory}/apply.result\ncat {directory}/apply.log\n')
    require(result.splitlines()[0]=='0' and 'C105_INSTALLED_ROOT_RO_NO_SERVICE_NO_TOKEN_NO_REBOOT' in result,
        'Apply failed: inspect rollback and retained capsule, never reapply')
    full=guard+health
    require(remote('after',full+INFRA)==(stage/'before.stdout').read_text(),'Infrastructure changed')
    remote('mounts-private',full+f'cmp /proc/1/mountinfo {directory}/mounts.before\ncmp {directory}/private.before {directory}/private.after\n')
    require(remote('caller-check',full+f'sh /{PREFIX}/caller.sh check\n')=='C105_CALLER_CHECK_OK_NO_UI\n','Native installed caller check')
    demo=remote('allocate-stage',full+'mktemp -d /run/muos-prefs-data.XXXXXX\n').strip()
    require(re.fullmatch('/run/muos-prefs-data[.][A-Za-z0-9]{6}',demo),'Finite dry stage')
    write('native-stage-directory',demo+'\n')
    code=full+f'''sh /{PREFIX}/caller.sh stage {demo}
printf 'C105_STAGE_READY\\n' | cmp -s - {demo}/caller-stage/ready
'''
    for n in SCRIPTS:code+=f'''cmp /{PREFIX}/{n} {demo}/{n}
[ "$(stat -c '%u:%g:%a:%h' {demo}/{n})" = 0:0:700:1 ]
'''
    code+=f'''if sh /{PREFIX}/caller.sh stage {demo};then exit 64;fi
if sh /{PREFIX}/caller.sh run {demo} observe;then exit 64;fi
echo C105_NATIVE_STAGE_AND_INCOMPLETE_RUN_REFUSAL_OK
'''
    native=remote('native-stage',code)
    require(native=='C105_CALLER_STAGE_OK_RAM_ONLY\nC105_NATIVE_STAGE_AND_INCOMPLETE_RUN_REFUSAL_OK\n','Native staging result')
    remote('cleanup-stage',full+f'''[ ! -L {demo} ];[ "$(stat -c '%u:%g:%a' {demo})" = 0:0:700 ]
! findmnt -rn -M {demo} >/dev/null
rm -rf {demo}
cmp /proc/1/mountinfo {directory}/mounts.before
''')
    write('collected-result.txt',result)
    remote('cleanup',full+f'''[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
! findmnt -rn -M {directory} >/dev/null
cmp /proc/1/mountinfo {directory}/mounts.before
rm -rf {directory}
echo C105_RAM_REMOVED_ROOT_RO
''')
    require(remote('post-cleanup-health',full+INFRA)==(stage/'before.stdout').read_text(),'Final health changed')
    completed={'passed':True,'schema':105,'boot_sequence':boot['boot_sequence'],'files_added':17,'directories_added':1,
        'existing_files_replaced':0,'bytes_added':report['bytes'],'root_read_only':True,'RAM_removed':True,
        'native_package_and_142_public_dependencies_checked':True,'native_stage_and_repeat_incomplete_run_refusal_passed':True,
        'private_state_fingerprint_matched':True,'infrastructure_and_global_mounts_preserved':True,
        'reboot_token_service_GUI_ROM_or_save_executed':False,'full_graphical_installed_caller_qualified':False,
        'plan_sha256':sha(stage/'plan.json'),'source_sha256':report['source_sha256'],
        'checks_sha256':sha(checks/'analysis.json'),'parent_proofs_sha256':report['parent_proofs_sha256']}
    write('analysis.json',json.dumps(completed,indent=2)+'\n');sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C105 manual caller installed and native check/stage/refusals passed; root RO:',stage)

if __name__=='__main__':main()
