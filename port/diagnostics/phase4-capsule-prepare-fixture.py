#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C107 synthetic RAM inputs with the real C105 stage/staged/asset functions."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys

source,out,old=map(Path,sys.argv[1:4]);base=Path('/tmp/c107');cap=Path('/run/muos-prefs-data.ABC123')
root=base/'root';pkg=root/'usr/libexec/muos-capsule';caller=root/'usr/libexec/muos-caller';cases=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashof=sha
contents=['functions.sh','assets.tsv','contract.json','LICENSE']
scripts=['adapter.sh','app-launch.sh','cycle.sh','frontend-libs.sh','installed-host.sh','installed-store.sh','select.sh','store-base.sh','store.sh','worker.sh']

def reset():
    cap.with_name('c107-extra-link').unlink(missing_ok=True)
    if base.exists():shutil.rmtree(base)
    if cap.is_symlink():cap.unlink()
    elif cap.exists():shutil.rmtree(cap)
    shutil.copytree(source,pkg);shutil.copytree(old,caller)
    for p in [root,root/'usr',root/'usr/libexec',pkg,caller]:p.chmod(0o755)
    cap.mkdir(mode=0o700);(cap/'inputs').mkdir(mode=0o700)
    core=root/'opt/muos/share/core/gambatte_libretro.so';core.parent.mkdir(parents=True);core.write_bytes(b'fixture core');core.chmod(0o644)
    for p in core.parents:
        if p==root:break
        p.chmod(0o755)
    rows=[]
    for _,mode,dest,origin in (line.split() for line in (pkg/'assets.tsv').read_text().splitlines()):
        src=cap/origin if origin.startswith('inputs/') else root/origin
        src.parent.mkdir(parents=True,exist_ok=True);src.write_bytes(origin.encode());src.chmod(int(mode,8))
        if origin.startswith('opt/'):
            for p in src.parents:
                if p==root:break
                p.chmod(0o755)
        rows.append((sha(src),mode,dest,origin))
    (cap/'inputs/private.gb').write_bytes(b'R'*32768);(cap/'inputs/private.gb').chmod(0o700)
    (pkg/'assets.tsv').write_text(''.join(' '.join(r)+'\n' for r in rows))
    (pkg/'payload.sha256').write_text(''.join(sha(pkg/n)+' '+n+'\n' for n in contents))
    (caller/'assets.tsv').write_text(''.join(h+' '+d+'\n' for h,_,d,_ in rows if d!='provider-probe'))
    (caller/'dependencies.tsv').write_text(sha(core)+' 644 '+str(core.stat().st_size)+' opt/muos/share/core/gambatte_libretro.so\n')
    old_contents=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE']
    (caller/'payload.sha256').write_text(''.join(sha(caller/n)+' '+n+'\n' for n in old_contents))
    for directory in [pkg,caller]:
        for p in directory.iterdir():p.chmod(0o644)
    return sha(pkg/'payload.sha256'),sha(caller/'payload.sha256'),sha(core)

def invoke(label,body='capsule_prepare "$3"',ok=True,change=None):
    manifest,old_manifest,core=reset()
    if change:change()
    script='''set -eu
umask 077
capsule_system_root=$1;capsule_package_root=$1/usr/libexec/muos-capsule;capsule_manifest_sha=$2;capsule_core_sha=$4
caller_system_root=$1;caller_root=$1/usr/libexec/muos-caller;caller_manifest_sha=$5
. "$caller_root/functions.sh"
. "$capsule_package_root/functions.sh"
caller_exec() { case "$1" in platform|capsule|staged) return 0;;boot) printf '81\\nfixture-UUID\\n';;*) return 64;;esac; }
copied=0
capsule_exec() {
 case "$1" in
 platform) [ "${FAIL_PLATFORM:-0}" = 0 ];;tmpfs) [ "${FAIL_TMPFS:-0}" = 0 ];;
 stage) [ "${FAIL_STAGE:-0}" = 0 ] && c105_stage "$2";;
 copied) copied=$((copied+1));[ "$copied" != "${FAIL_COPY:-0}" ];;
 staged) [ "${FAIL_FINAL:-0}" = 0 ] && c105_staged "$2" && c105_assets "$2";;
 *) return 64;;esac
}
'''
    r=subprocess.run(['sh','-c',script+body,'fixture',str(root),manifest,str(cap),core,old_manifest],capture_output=True,text=True)
    (out/(label+'.log')).write_text(r.stdout+r.stderr)
    assert (r.returncode==0)==ok,(label,r.returncode,r.stdout,r.stderr)
    cases.append(label);return r

invoke('complete-preparation-through-real-C105-functions')
core=sha(root/'opt/muos/share/core/gambatte_libretro.so');rom=sha(cap/'private.gb')
expected=hashlib.sha256(b'MUOS-R35S-GB-SNAPSHOT-V1\0'+bytes.fromhex(core)+bytes.fromhex(rom)).hexdigest()
assert (cap/'identity').read_text()==expected+'\n'
assert (cap/'role').read_text()=='load\n' and (cap/'preparation.once/ready').read_text()=='C107_CAPSULE_READY\n'
assert (cap/'gb-assets.sha256').read_text()==core+'  /opt/muos/share/core/gambatte_libretro.so\n'+rom+'  private.gb\n'
cases.append('identity-and-ROM-manifest-match-independent-Python-contract')
for label,change in {
 'package-tamper':lambda:(pkg/'contract.json').write_text('bad'),
 'manifest-tamper':lambda:(pkg/'payload.sha256').write_text('bad'),
 'package-neighbor':lambda:(pkg/'unknown').write_text('keep'),
 'bad-public-input':lambda:(cap/'inputs/runner').write_bytes(b'bad'),
 'input-mode':lambda:(cap/'inputs/state-metadata').chmod(0o755),
 'input-alias':lambda:((cap/'inputs/runner').unlink(),(cap/'inputs/runner').symlink_to('state-metadata')),
 'input-hardlink':lambda:os.link(cap/'inputs/runner',cap.with_name('c107-extra-link')),
 'ROM-too-small':lambda:(cap/'inputs/private.gb').write_bytes(b'tiny'),
 'ROM-alias':lambda:((cap/'inputs/private.gb').unlink(),(cap/'inputs/private.gb').symlink_to('runner')),
 'inputs-neighbor':lambda:(cap/'inputs/unknown').write_text('foreign'),
 'inputs-mode':lambda:(cap/'inputs').chmod(0o755),
 'capsule-neighbor':lambda:(cap/'foreign').write_text('foreign'),
 'core-changed':lambda:(root/'opt/muos/share/core/gambatte_libretro.so').write_bytes(b'bad'),
 'installed-library-changed':lambda:(root/'opt/muos/frontend/lib/libui.so').write_bytes(b'bad'),
 'installed-parent-mode':lambda:(root/'opt/muos/frontend/lib').chmod(0o777),
}.items():invoke('reject-'+label,ok=False,change=change)
for name in ['PLATFORM','TMPFS','STAGE','FINAL']:
    invoke('failure-'+name,'FAIL_'+name+'=1;capsule_prepare "$3"',False)
for n in [1,7,11,12]:
    invoke('partial-copy-'+str(n),f'FAIL_COPY={n};if capsule_prepare "$3";then exit 1;fi;[ -d "$3/preparation.once" ];[ ! -e "$3/preparation.once/ready" ]')
invoke('never-retry-preparation','capsule_prepare "$3";capsule_prepare "$3"',False)
invoke('reject-path-injection','capsule_prepare /run/muos-prefs-data.bad/xx',False)
invoke('invalid-identity-input','capsule_identity nope '+'a'*64,False)

# Run the actual derived transaction for the NEW six-leaf scope, with the
# same media-only callback mocks as C105. Do not rerun C105's runtime suite.
tx_source=Path('/port/diagnostics/phase4-manual-caller-fixture.py').read_text().split('# Exercise the derived C76 transaction',1)[1]
tx_source='# Exercise the derived C76 transaction'+tx_source
old_names="names=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE','payload.sha256','caller.sh']"
assert tx_source.count(old_names)==1
tx_source=tx_source.replace(old_names,"names=['functions.sh','assets.tsv','contract.json','LICENSE','payload.sha256','prepare.sh']")
tx_source=tx_source.replace('usr/libexec/muos-caller','usr/libexec/muos-capsule')
tx_source=tx_source.replace('c105','c108').replace('C105','C108').replace("worker.sh","functions.sh")
tx_source=tx_source.replace('[1,9,17]','[1,3,6]').replace('17-leaf','6-leaf')
exec(compile(tx_source,__file__+'-transaction','exec'),globals())
