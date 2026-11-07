#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C113 exact new shelf, no overwrite, failure retention, existing tree unchanged."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
source,out,binary=map(Path,sys.argv[1:4]);base=Path('/tmp/c113');cap=base/'cap';data=base/'data';cases=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def reset():
 if base.exists():shutil.rmtree(base)
 cap.mkdir(parents=True,mode=0o700);(data/'MUOS/preferences').mkdir(parents=True)
 (data/'MUOS').chmod(0o700);(data/'MUOS/preferences').chmod(0o700)
 (data/'MUOS/preferences/preferences').write_text('original-preferences');(data/'MUOS/preferences/preferences').chmod(0o600)
 (cap/'private.gb').write_bytes(b'R'*65536);(cap/'private.gb').chmod(0o600)
 (cap/'ROM.sha256').write_text(sha(cap/'private.gb')+'  gb/private.gb\n');(cap/'ROM.sha256').chmod(0o600)
 shutil.copyfile(binary,cap/'sync-path');(cap/'sync-path').chmod(0o700)
def invoke(label,body='rom_inventory > "$rom_cap/before";rom_write;rom_inventory > "$rom_cap/after";cmp "$rom_cap/before" "$rom_cap/after";rom_check "$rom_mount/MUOS/port-roms-v1"',ok=True,change=None,hook='never',at=1):
 reset()
 if change:change()
 script='''set -eu
umask 077
rom_cap=$1;rom_mount=$2
. "$3"
count=0
rom_exec() {
 if [ "$1" = "$FAIL_HOOK" ];then count=$((count+1));[ "$count" != "$FAIL_AT" ] || return 1;fi
 case "$1" in sync) shift;qemu-aarch64 -cpu cortex-a35 -L /work/graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot "$rom_cap/sync-path" "$@";;*) return 0;;esac
}
'''
 env={**os.environ,'FAIL_HOOK':hook,'FAIL_AT':str(at)}
 r=subprocess.run(['sh','-c',script+body,'fixture',str(cap),str(data),str(source)],capture_output=True,text=True,env=env)
 (out/(label+'.log')).write_text(r.stdout+r.stderr)
 assert (r.returncode==0)==ok,(label,r.returncode,r.stderr)
 assert (data/'MUOS/preferences/preferences').read_text()=='original-preferences'
 cases.append(label)
invoke('new-private-shelf-and-full-existing-tree-byte-identical')
assert (data/'MUOS/port-roms-v1/gb/private.gb').read_bytes()==b'R'*65536
invoke('no-second-import','rom_write;rom_write',False)
for name,change in {
 'existing-final':lambda:(data/'MUOS/port-roms-v1').mkdir(),
 'existing-staging':lambda:(data/'MUOS/.port-roms-v1.new').mkdir(),
 'final-alias':lambda:(data/'MUOS/port-roms-v1').symlink_to(data/'MUOS/preferences'),
 'staging-alias':lambda:(data/'MUOS/.port-roms-v1.new').symlink_to(data/'MUOS/preferences'),
 'parent-mode':lambda:(data/'MUOS').chmod(0o777),
 'bad-ROM-hash':lambda:(cap/'private.gb').write_bytes(b'bad'),
 'ROM-mode':lambda:(cap/'private.gb').chmod(0o644),
 'ROM-hardlink':lambda:os.link(cap/'private.gb',cap/'other'),
 'ROM-alias':lambda:((cap/'private.gb').unlink(),(cap/'private.gb').symlink_to('ROM.sha256')),
 'registry-path':lambda:(cap/'ROM.sha256').write_text('0'*64+'  ../private.gb\n'),
 'registry-extra':lambda:(cap/'ROM.sha256').write_text((cap/'ROM.sha256').read_text()+'\n'),
}.items():invoke('reject-'+name,ok=False,change=change)
for hook,at in [('directory-created',1),('ROM-copied',1),('sync',1),('sync',2),('before-publish',1),('after-publish',1),('sync',3)]:
 invoke('retain-failure-'+hook+'-'+str(at),'if rom_write;then exit 1;fi;[ -d "$rom_mount/MUOS/.port-roms-v1.new" ] || [ -d "$rom_mount/MUOS/port-roms-v1" ];if rom_write;then exit 1;fi',hook=hook,at=at)
invoke('detect-foreign-file-mutation','rom_inventory > "$rom_cap/before";printf altered > "$rom_mount/MUOS/preferences/preferences";rom_inventory > "$rom_cap/after";if cmp "$rom_cap/before" "$rom_cap/after";then exit 1;fi;printf original-preferences > "$rom_mount/MUOS/preferences/preferences"')
(out/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
 'existing_files_preserved':True,'private_content_used':False,'real_media_or_namespace_used':False,
 'sync_helper_A35_QEMU_used':True,'power_loss_tested':False},indent=2)+'\n')
print('C113 fixtures:',len(cases),'passed')
