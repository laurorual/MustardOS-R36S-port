#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C112 synthetic resident package/ROM source and real additive transaction."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
source,out=map(Path,sys.argv[1:3]);base=Path('/tmp/c112');root=base/'root';pkg=root/'usr/libexec/muos-resident'
cap=Path('/run/muos-prefs-data.ABC123');data=base/'data';cases=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashof=sha
names=['functions.sh','assets.tsv','dependencies.tsv','contract.json','LICENSE','LICENSE.frontend','runner','state-metadata','menu-libmuxmod.so','provider-probe','sync-path','payload.sha256','load.sh']
contents=names[:-2]
def reset():
 if base.exists():shutil.rmtree(base)
 if cap.is_symlink():cap.unlink()
 elif cap.exists():shutil.rmtree(cap)
 cap.with_name('resident-link').unlink(missing_ok=True)
 shutil.copytree(source,pkg)
 for p in [root,root/'usr',root/'usr/libexec',pkg]:p.chmod(0o755)
 cap.mkdir(mode=0o700)
 for n in ['runner','state-metadata','menu-libmuxmod.so','provider-probe']:(pkg/n).write_bytes(n.encode())
 dep=root/'dep';dep.write_text('dependency');dep.chmod(0o644)
 (pkg/'dependencies.tsv').write_text(sha(dep)+' 644 dep\n')
 (pkg/'assets.tsv').write_text(''.join(sha(pkg/n)+' '+n+'\n' for n in ['runner','state-metadata','menu-libmuxmod.so','provider-probe']))
 (pkg/'payload.sha256').write_text(''.join(sha(pkg/n)+' '+n+'\n' for n in contents))
 for p in pkg.iterdir():p.chmod(0o644)
 rr=data/'MUOS/port-roms-v1';(rr/'gb').mkdir(parents=True)
 for p in [rr,rr/'gb']:p.chmod(0o700)
 (rr/'gb/private.gb').write_bytes(b'R'*32768);(rr/'gb/private.gb').chmod(0o600)
 (rr/'.muos-rom-root-v1').write_text('MUOS-R35S-ROM-ROOT-V1\n');(rr/'.muos-rom-root-v1').chmod(0o600)
 (rr/'ROM.sha256').write_text(sha(rr/'gb/private.gb')+'  gb/private.gb\n');(rr/'ROM.sha256').chmod(0o600)
 return sha(pkg/'payload.sha256')

def invoke(label,body='resident_prepare "$3"',ok=True,change=None):
 manifest=reset()
 if change:change()
 text='''set -eu
umask 077
resident_system_root=$1;resident_root=$1/usr/libexec/muos-resident;resident_manifest_sha=$2;fixture_data=$4
. "$resident_root/functions.sh"
resident_exec() {
 case "$1" in
 platform) [ "${FAIL_PLATFORM:-0}" = 0 ];;
 read-rom) [ "${FAIL_READ:-0}" = 0 ] && resident_rom_copy "$fixture_data" "$2";;
 prepare) [ "${FAIL_PREPARE:-0}" = 0 ] && [ ! -e "$2/data" ] && mkdir -m 700 "$2/preparation.once" && printf 'C107_CAPSULE_READY\\n' > "$2/preparation.once/ready";;
 *) return 64;;esac
}
'''
 r=subprocess.run(['sh','-c',text+body,'fixture',str(root),manifest,str(cap),str(data)],capture_output=True,text=True)
 (out/(label+'.log')).write_text(r.stdout+r.stderr)
 assert (r.returncode==0)==ok,(label,r.returncode,r.stdout,r.stderr)
 cases.append(label)

invoke('resident-preparation-and-private-ROM-byte-exact')
assert (cap/'inputs/private.gb').read_bytes()==b'R'*32768
assert (cap/'preparation.once/resident').read_text()=='C112_RESIDENT_INPUTS_READY_ROM_P3\n'
assert (cap/'inputs/private.gb').stat().st_mode&0o777==0o700
rr=lambda:data/'MUOS/port-roms-v1'
for n,f in {
 'package-hash':lambda:(pkg/'contract.json').write_text('bad'),
 'package-mode':lambda:(pkg/'runner').chmod(0o755),
 'package-neighbor':lambda:(pkg/'foreign').write_text('keep'),
 'dependency-changed':lambda:(root/'dep').write_text('bad'),
 'nonempty-capsule':lambda:(cap/'foreign').write_text('keep'),
 'capsule-mode':lambda:cap.chmod(0o755),
 'capsule-alias':lambda:(shutil.rmtree(cap),cap.symlink_to(base)),
 'ROM-content':lambda:(rr()/'gb/private.gb').write_bytes(b'bad'),
 'ROM-mode':lambda:(rr()/'gb/private.gb').chmod(0o644),
 'ROM-alias':lambda:((rr()/'gb/private.gb').unlink(),(rr()/'gb/private.gb').symlink_to('../ROM.sha256')),
 'ROM-hardlink':lambda:os.link(rr()/'gb/private.gb',base/'extra-link'),
 'ROM-directory-mode':lambda:(rr()/'gb').chmod(0o755),
 'ROM-MUOS-parent-mode':lambda:(data/'MUOS').chmod(0o777),
 'ROM-root-alias':lambda:(rr().rename(base/'other'),rr().symlink_to(base/'other')),
 'ROM-extra':lambda:(rr()/'gb/extra').write_text('keep'),
 'registry-hash':lambda:(rr()/'ROM.sha256').write_text('0'*64+'  gb/private.gb\n'),
 'registry-path':lambda:(rr()/'ROM.sha256').write_text('0'*64+'  ../private.gb\n'),
 'registry-extra-line':lambda:(rr()/'ROM.sha256').write_text((rr()/'ROM.sha256').read_text()+'\n'),
 'registry-mode':lambda:(rr()/'ROM.sha256').chmod(0o644),
 'marker-wrong':lambda:(rr()/'.muos-rom-root-v1').write_text('bad'),
 'marker-alias':lambda:((rr()/'.muos-rom-root-v1').unlink(),(rr()/'.muos-rom-root-v1').symlink_to('ROM.sha256')),
}.items():invoke('reject-'+n,ok=False,change=f)
for n in ['PLATFORM','READ','PREPARE']:invoke('failure-'+n,'FAIL_'+n+'=1;resident_prepare "$3"',False)
invoke('no-retry-over-partial-capsule','resident_prepare "$3";resident_prepare "$3"',False)
invoke('input-hash-guard','resident_prepare "$3";printf bad > "$3/inputs/runner";resident_inputs "$3" 5',False)
# The native reader is separate from the global C111 stage: never weaken
# c25_media's original namespace requirement to read the internal ROM.
entry=(source/'load.sh').read_text()
assert 'resident_exec platform && resident_exec prepare' in (source/'functions.sh').read_text()
reader=entry.split(' read-rom:2)',1)[1].split(' *) exit 64',1)[0]
assert 'prefs_data_source' in reader and 'prefs_data_mounted ro' in reader and 'ro,noload,nosuid,nodev,noexec' in reader
assert 'umount' in reader and 'rmdir' in reader and '-o rw' not in entry
cases.append('native-reader-RO-private-and-unmounted-before-global-C111-delegation')
# Exercise the new AArch64 fsync helper on real container tmpfs, not media.
helper=Path('/tmp/sync-path');shutil.copyfile(source/'sync-path',helper);helper.chmod(0o700)
qemu=['qemu-aarch64','-cpu','cortex-a35','-L','/work/graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot',str(helper)]
for label,args,code in [('file',[str(cap/'inputs/runner')],0),('directory',[str(cap)],0),('no-args',[],64),
 ('relative',['relative'],64),('missing',['/tmp/missing-sync-input'],64)]:
 result=subprocess.run(qemu+args,capture_output=True,text=True);assert result.returncode==code,(label,result.returncode,result.stderr)
 cases.append('A35-sync-'+label)
# Exercise the same real transaction engine for the new 13-file scope.
scripts=[]
tx=Path('/port/diagnostics/phase4-manual-caller-fixture.py').read_text().split('# Exercise the derived C76 transaction',1)[1]
tx='# Exercise the derived C76 transaction'+tx
old="names=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE','payload.sha256','caller.sh']"
assert tx.count(old)==1;tx=tx.replace(old,'names='+repr(names))
tx=tx.replace('usr/libexec/muos-caller','usr/libexec/muos-resident').replace('c105','c112').replace('C105','C112')
tx=tx.replace('[1,9,17]','[1,7,13]').replace('17-leaf','13-leaf').replace('worker.sh','functions.sh')
exec(compile(tx,__file__+'-transaction','exec'),globals())
