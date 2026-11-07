#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C105 installed caller contracts/failures on disposable root and RAM capsule."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys

source=Path(sys.argv[1]);out=Path(sys.argv[2]);cases=[]
base=Path('/tmp/c105');root=base/'root';pkg=root/'usr/libexec/muos-caller';cap=Path('/run/muos-prefs-data.ABC123')
scripts=['adapter.sh','app-launch.sh','cycle.sh','frontend-libs.sh','installed-host.sh','installed-store.sh','select.sh','store-base.sh','store.sh','worker.sh']
content=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE']
hashof=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def reset():
    if base.exists():shutil.rmtree(base)
    if cap.is_symlink():cap.unlink()
    elif cap.exists():shutil.rmtree(cap)
    pkg.mkdir(parents=True);shutil.copytree(source,pkg,dirs_exist_ok=True)
    for p in [root,root/'usr',root/'usr/libexec',pkg]:p.chmod(0o755)
    (root/'usr/bin').mkdir(mode=0o755);dep=root/'usr/bin/dep';dep.write_bytes(b'public dependency');dep.chmod(0o644)
    (pkg/'dependencies.tsv').write_text(hashof(dep)+' 644 17 usr/bin/dep\n')
    assets=['runner','state-metadata',*[d+'/'+n for d in ['lib','provider-lib'] for n in ['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so']]]
    (pkg/'assets.tsv').write_text(''.join(hashlib.sha256(n.encode()).hexdigest()+' '+n+'\n' for n in assets))
    (pkg/'payload.sha256').write_text(''.join(hashof(pkg/n)+' '+n+'\n' for n in content))
    for p in pkg.iterdir():p.chmod(0o644)
    cap.mkdir(mode=0o700)
    return hashof(pkg/'payload.sha256')

def invoke(label,script,ok=True,prep=None):
    digest=reset()
    if prep:prep()
    prefix='''set -eu
umask 077
caller_system_root=$1;caller_root=$1/usr/libexec/muos-caller;caller_manifest_sha=$2
. /port/device/rk-r35s-p0/manual-caller/functions.sh
counter=0
caller_exec() {
 case "$1" in
 platform) [ "${FAIL_PLATFORM:-0}" = 0 ];;
 capsule) return 0;;
 boot) printf '%s\\n' "${BOOT:-79}" fixed-UUID;;
 staged) counter=$((counter+1));[ "$counter" != "${FAIL_AT:-0}" ];;
 run) echo C105_FIXTURE_RUN_HOOK;;
 *) return 64;;esac
}
'''
    r=subprocess.run(['sh','-c',prefix+script,'fixture',str(root),digest,str(cap)],capture_output=True,text=True)
    (out/(label+'.log')).write_text(r.stdout+r.stderr)
    assert (r.returncode==0)==ok,(label,r.returncode,r.stdout,r.stderr)
    cases.append(label);return r

invoke('valid-package-and-dependency','c105_package;c105_dependencies')
for name,prep in {
    'manifest-changed':lambda:(pkg/'payload.sha256').write_text('changed'),
    'source-changed':lambda:(pkg/'worker.sh').write_text('changed'),
    'source-mode':lambda:(pkg/'worker.sh').chmod(0o755),
    'source-alias':lambda:((pkg/'worker.sh').unlink(),(pkg/'worker.sh').symlink_to('adapter.sh')),
    'source-hardlink':lambda:os.link(pkg/'worker.sh',base/'neighbor'),
    'foreign-package-file':lambda:(pkg/'foreign').write_text('foreign'),
    'package-mode':lambda:pkg.chmod(0o777),
}.items():invoke('reject-'+name,'c105_package',False,prep)
invoke('reject-dependency-change','c105_dependencies',False,lambda:(root/'usr/bin/dep').write_text('changed'))
invoke('valid-RAM-stage','c105_stage "$3";c105_staged "$3"')
invoke('stage-refuses-platform','FAIL_PLATFORM=1;c105_stage "$3"',False)
invoke('stage-refuses-existing-script','c105_stage "$3"',False,lambda:(cap/'worker.sh').write_text('foreign'))
invoke('stage-never-overwrites-or-repeats','c105_stage "$3";c105_stage "$3"',False)
invoke('stage-retains-partial-no-ready','FAIL_AT=3;if c105_stage "$3";then exit 1;fi;[ -e "$3/cycle.sh" ];[ ! -e "$3/caller-stage/ready" ]')
invoke('reject-changed-staged-script','c105_stage "$3";printf changed > "$3/cycle.sh";c105_staged "$3"',False)
invoke('reject-staged-symlink','c105_stage "$3";rm "$3/cycle.sh";ln -s adapter.sh "$3/cycle.sh";c105_staged "$3"',False)
invoke('reject-stale-boot','c105_stage "$3";BOOT=80;c105_staged "$3"',False)
invoke('reject-path-traversal','c105_stage /run/muos-prefs-data.ab/cde',False)
invoke('reject-extra-run-mode','c105_run "$3" cycle',False)

def inputs():
    for d in ['lib','provider-lib','state','owner','watchdog']:(cap/d).mkdir(mode=0o700)
    for _,n in (line.split() for line in (pkg/'assets.tsv').read_text().splitlines()):
        p=cap/n;p.write_bytes(n.encode());p.chmod(0o700)
    values={'role':'load\n','identity':'a'*64+'\n','gb-assets.sha256':'fixture manifest\n',
        'launcher.sha256':hashof(pkg/'app-launch.sh')+'\n','store-base.sha256':hashof(pkg/'store-base.sh')+'\n',
        'installed-store.sha256':hashof(pkg/'installed-store.sh')+'\n'}
    for n,data in values.items():(cap/n).write_text(data);(cap/n).chmod(0o600)
    (cap/'private.gb').write_bytes(b'\0'*32768);(cap/'private.gb').chmod(0o700)

r=invoke('valid-run-only-through-hook','c105_stage "$3";c105_run "$3" observe',prep=inputs)
assert r.stdout=='C105_FIXTURE_RUN_HOOK\n'
for name,change in {
    'asset-changed':'printf changed > "$3/runner"',
    'asset-alias':'rm "$3/runner";ln -s state-metadata "$3/runner"',
    'foreign-library':'printf foreign > "$3/lib/evil.so"',
    'save-role':'printf "save\\n" > "$3/role"',
    'host-fallback':'printf foreign > "$3/muxretro"',
    'wrong-launcher':'printf bad > "$3/launcher.sha256"',
    'ROM-alias':'rm "$3/private.gb";ln -s runner "$3/private.gb"',
    'stale-package':'printf old > "$3/caller-stage/package"',
}.items():invoke('run-refuses-'+name,'c105_stage "$3";'+change+';c105_run "$3" observe',False,inputs)
invoke('run-one-shot','c105_stage "$3";c105_run "$3" observe;c105_run "$3" observe',False,inputs)

# Exercise the derived C76 transaction on the NEW one-directory/17-leaf scope.
# Only callbacks for media/remount/fingerprint are replaced in this fixture.
install_base=Path('/tmp/c105-install')
transaction=source.parents[3]/'transaction.sh'
def install_case(label,hook='never',at=1,foreign=False):
    if install_base.exists():shutil.rmtree(install_base)
    ir=install_base/'root';ip=install_base/'payload';state=install_base/'state'
    (ir/'usr/libexec').mkdir(parents=True);state.mkdir();(ip/'new/usr/libexec/muos-caller').mkdir(parents=True)
    for d in [ir,ir/'usr',ir/'usr/libexec']:d.chmod(0o755)
    (ir/'foundation').write_bytes(b'unchanged')
    (ip/'foundation.sha256').write_text(hashof(ir/'foundation')+'  foundation\n')
    names=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE','payload.sha256','caller.sh']
    for n in names:
        p=ip/'new/usr/libexec/muos-caller'/n;shutil.copyfile(source/n,p);p.chmod(0o644)
    (ip/'FILES').write_text(''.join(hashof(ip/'new/usr/libexec/muos-caller'/n)+' 644 usr/libexec/muos-caller/'+n+'\n' for n in names))
    text='''set -eu
umask 077
install_root=$1;install_payload=$2;install_state=$3;install_rw=0
. "$4"
count=0;failed=0
install_exec() {
 case "$1" in rw) install_rw=1;;esac
 if [ "$1" = "$5" ];then
  count=$((count+1))
  if [ "$count" = "$6" ] && [ "$failed" = 0 ];then failed=1;return 1;fi
 fi
 return 0
}
'''
    # Save test configuration outside the callback's own positional arguments.
    text=text.replace('if [ "$1" = "$5" ];then','if [ "$1" = "$FAIL_HOOK" ];then').replace('[ "$count" = "$6" ]','[ "$count" = "$FAIL_AT" ]')
    text+='''rc=0;c105_apply || rc=$?
'''
    if foreign:
        text+='''[ "$rc" = 0 ];printf foreign > "$install_root/usr/libexec/muos-caller/foreign"
install_rw=1
if c105_rollback;then exit 1;fi
[ "$(cat "$install_root/usr/libexec/muos-caller/foreign")" = foreign ]
[ -f "$install_root/usr/libexec/muos-caller/worker.sh" ]
'''
    elif hook=='never':
        text+='''[ "$rc" = 0 ];c105_verify;install_rw=1;c105_rollback;c105_absent
'''
    else:
        text+='''[ "$rc" != 0 ];[ "$install_rw" = 0 ] || c105_rollback;c105_absent
'''
    env={**os.environ,'FAIL_HOOK':hook,'FAIL_AT':str(at)}
    result=subprocess.run(['sh','-c',text,'fixture',str(ir),str(ip),str(state),str(transaction)],env=env,capture_output=True,text=True)
    (out/(label+'.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0,(label,result.stdout,result.stderr)
    cases.append(label)

install_case('install-new-17-leaf-scope-and-exact-rollback')
for step in ['guard','rw','directory-created','verify','sync','ro']:
    install_case('install-failure-'+step,step)
for step in ['file-staged','file-installed']:
    for at in [1,9,17]:install_case('install-failure-'+step+'-'+str(at),step,at)
install_case('install-rollback-preserves-foreign-neighbor',foreign=True)
(out/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'platform_tmpfs_and_run_callbacks_mocked':True,'core_ROM_namespace_or_reboot_executed':False},indent=2)+'\n')
print('C105 caller fixture cases:',len(cases))
