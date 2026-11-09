#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C119 real staged adoption/rollback-boundary tests inside tmpfs container."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
plan=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);os.umask(0o077)
base=Path('/tmp/c119');root=base/'root';legacy=root/'usr/libexec/muos-caller';cap=Path('/run/muos-prefs-data.ABC123')
v2=cap/'contract-v2';cases=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scripts=plan['scripts']

def restore(p):
    if p.is_symlink():return
    os.chown(p,0,0)
    if p.is_dir():
        p.chmod(0o700)
        for q in p.iterdir():restore(q)

def put(p,data,mode):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode());p.chmod(mode)

def reset():
    for p in [base,cap]:
        if p.exists():restore(p);shutil.rmtree(p)
    legacy.mkdir(parents=True);cap.mkdir(mode=0o700)
    for p in [root,*root.rglob('*')]:
        if p.is_dir():p.chmod(0o755)
    for n in scripts:put(legacy/n,'C105 fixture '+n+'\n',0o644)
    put(legacy/'functions.sh',Path('/port/device/rk-r35s-p0/manual-caller/functions.sh').read_bytes(),0o644)
    dep=root/'usr/share/fixture-public';put(dep,'public dependency',0o644)
    for p in dep.parents:
        if p==root.parent:break
        p.chmod(0o755)
    put(legacy/'dependencies.tsv',f'{sha(dep)} 644 {dep.stat().st_size} usr/share/fixture-public\n',0o644)
    assets=['runner','state-metadata',*[d+'/'+n for d in ['lib','provider-lib'] for n in ['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so']]]
    for n in assets:put(cap/n,'C119 asset '+n,0o700)
    for d in ['lib','provider-lib','state','owner','watchdog']:(cap/d).mkdir(mode=0o700,exist_ok=True);(cap/d).chmod(0o700)
    put(legacy/'assets.tsv',''.join(sha(cap/n)+' '+n+'\n' for n in assets),0o644)
    for n in ['contract.json','LICENSE','caller.sh']:put(legacy/n,n,0o644)
    contents=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE']
    put(legacy/'payload.sha256',''.join(sha(legacy/n)+' '+n+'\n' for n in contents),0o644)
    for n in ['identity','role','launcher.sha256','store-base.sha256','installed-store.sha256','gb-assets.sha256']:put(cap/n,'fixture\n',0o600)
    put(cap/'role','load\n',0o600);put(cap/'private.gb',b'R'*65536,0o700)
    for marker,n in [('launcher','app-launch.sh'),('store-base','store-base.sh'),('installed-store','installed-store.sh')]:put(cap/(marker+'.sha256'),sha(legacy/n)+'\n',0o600)
    (cap/'preparation.once').mkdir(mode=0o700)
    put(cap/'preparation.once/ready','C107_CAPSULE_READY\n',0o600);put(cap/'preparation.once/resident','C112_RESIDENT_INPUTS_READY_ROM_P3\n',0o600)
    v2.mkdir(mode=0o700)
    for n,text in plan['bundle'].items():put(v2/n,text,0o644)
    r=invoke('c105_stage "$v2_cap"');assert r.returncode==0,(r.stdout,r.stderr)

def invoke(command,extra=''):
    code=f'''set -eu
umask 077
caller_system_root={root};caller_root={legacy};caller_manifest_sha={sha(legacy/'payload.sha256')}
v2_cap={cap};v2_root={v2};v2_manifest_sha={sha(v2/'payload.sha256')}
. {legacy}/functions.sh
. /port/device/rk-r35s-p0/batch-caller/functions.sh
caller_exec() {{
 case "$1" in
 platform) [ "${{FAIL_PLATFORM:-0}}" = 0 ];;
 capsule) [ "$(findmnt -rn -T "$2" -o FSTYPE)" = tmpfs ];;
 boot) printf '%s\\nfixture-boot\\n' "${{FIXTURE_BOOT:-83}}";;
 staged) return 0;;
 *) return 64;;esac
}}
'''
    return subprocess.run(['sh','-c',code+extra+'\n'+command],capture_output=True,text=True,timeout=8)

def snapshot():
    result={}
    for p in cap.rglob('*'):
        s=p.lstat()
        try:data=os.readlink(p) if p.is_symlink() else sha(p) if p.is_file() else ''
        except PermissionError:data='unreadable-by-fixture'
        result[str(p.relative_to(cap))]=(s.st_mode,s.st_uid,s.st_gid,s.st_nlink,data)
    return result

reset();assert invoke('c119_adopt "$v2_cap";c119_staged "$v2_cap"').returncode==0
assert invoke('c105_staged "$v2_cap"').returncode!=0
assert (cap/'installed-host.sh').read_bytes()==(v2/'host.sh').read_bytes()
assert all((cap/'caller-stage'/n).read_bytes()==(cap/'caller-v2-before'/n).read_bytes() for n in ['ready','boot','package'])
cases.append('adopted-host-new-stage-old-stage-backup-intact-and-old-staged-refuses-mixed')
before=snapshot();assert invoke('c119_adopt "$v2_cap"').returncode!=0;assert before==snapshot();cases.append('repeat-adoption-refused-byte-and-metadata-exact')
for label,change in {
 'old-host-corrupt':lambda:put(cap/'installed-host.sh','bad',0o700),
 'old-host-link':lambda:((cap/'installed-host.sh').rename(cap/'other'),(cap/'installed-host.sh').symlink_to(cap/'other')),
 'old-stage-boot':lambda:put(cap/'caller-stage/boot','wrong',0o600),
 'run-consumed':lambda:(cap/'caller-stage/run.once').mkdir(),
 'already-selected':lambda:put(cap/'selection.once','',0o600),
 'legacy-marker':lambda:put(cap/'preparation.once/resident','bad',0o600),
 'marker-mode':lambda:(cap/'preparation.once/ready').chmod(0o644),
 'bundle-extra':lambda:put(v2/'extra','x',0o644),
 'bundle-hash':lambda:put(v2/'host.sh','bad',0o644),
 'bundle-mode':lambda:(v2/'host.sh').chmod(0o700),
 'bundle-hardlink':lambda:os.link(v2/'host.sh',cap/'extra-link'),
 'role-save':lambda:put(cap/'role','save\n',0o600),
 'asset-bad':lambda:put(cap/'runner','bad',0o700),
}.items():
    reset();change();before=snapshot();r=invoke('c119_adopt "$v2_cap"')
    assert r.returncode!=0 and before==snapshot() and not (cap/'caller-v2-stage').exists(),(label,r.stderr)
    cases.append('pre-adopt-'+label+'-refused-without-mutation')
reset();before=snapshot();assert invoke('c119_adopt "$v2_cap"','FAIL_PLATFORM=1').returncode!=0 and before==snapshot();cases.append('platform-refused-without-mutation')
reset();before=snapshot();assert invoke('c119_adopt /run/muos-prefs-data.OTHER1').returncode!=0 and before==snapshot();cases.append('cross-capsule-refused')
for label,change in {
 'new-host-old-bytes':lambda:put(cap/'installed-host.sh',(legacy/'installed-host.sh').read_bytes(),0o700),
 'new-host-mode':lambda:(cap/'installed-host.sh').chmod(0o644),
 'new-host-owner':lambda:os.chown(cap/'installed-host.sh',1,0),
 'new-host-hardlink':lambda:os.link(cap/'installed-host.sh',cap/'new-link'),
 'other-script':lambda:put(cap/'app-launch.sh','bad',0o700),
 'new-stage-boot':lambda:put(cap/'caller-v2-stage/boot','wrong',0o600),
 'new-stage-mode':lambda:(cap/'caller-v2-stage/ready').chmod(0o644),
 'new-run-once':lambda:(cap/'caller-v2-stage/run.once').mkdir(),
 'reservation-marker':lambda:put(cap/'caller-stage/run.once/adopted-by-c119','bad',0o600),
 'reservation-mode':lambda:(cap/'caller-stage/run.once').chmod(0o755),
 'reservation-extra':lambda:put(cap/'caller-stage/run.once/extra','x',0o600),
 'backup-host':lambda:put(cap/'caller-v2-before/installed-host.sh','bad',0o700),
}.items():
    reset();assert invoke('c119_adopt "$v2_cap"').returncode==0;change();before=snapshot()
    assert invoke('c119_staged "$v2_cap"').returncode!=0 and before==snapshot(),label
    cases.append('post-adopt-'+label+'-refused')
reset();assert invoke('c119_adopt "$v2_cap"').returncode==0
assert invoke('c119_staged "$v2_cap"','FIXTURE_BOOT=84').returncode!=0;cases.append('changed-boot-refused')
reset();fake=base/'bin';fake.mkdir();put(fake/'mv','#!/bin/sh\nexit 74\n',0o755)
r=invoke('c119_adopt "$v2_cap"',f'PATH={fake}:$PATH');assert r.returncode!=0 and (cap/'caller-v2-stage').is_dir()
before=snapshot();assert invoke('c119_adopt "$v2_cap"').returncode!=0 and before==snapshot();cases.append('partial-rename-failure-claim-retained-no-retry')
for args in [['run',str(cap),'observe'],['stage',str(cap)],['unknown']]:
    r=subprocess.run(['sh',str(v2/'caller.sh'),*args],capture_output=True,text=True);assert r.returncode==64
cases.append('full-entry-run-stage-and-unknown-refused-before-platform')
(out/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,'uid':os.getuid()},indent=2)+'\n')
print('C119',len(cases),'real adoption/refusal fixtures passed')
