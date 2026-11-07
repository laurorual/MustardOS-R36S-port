#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Restore original nav/confirm/back while keeping C06 rate-reference activity."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';base=work/'linux-diagnostic/frontend-audio-compare.ln84xpst'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
stage=Path(tempfile.mkdtemp(prefix='frontend-native-effects.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir();shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
name='usr/libexec/muos-c06-session';text=(repo/'port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh').read_text();assert text.count('c06_control_effects=1')==1
p=assets/name.replace('/','_');p.write_text(text.replace('c06_control_effects=1','c06_control_effects=0'))
entry={'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(base/'extracted'/name),'mode':0o755}
(stage/'debugfs.commands').write_text(f'rm /{name}\nwrite assets/{p.name} /{name}\nset_inode_field /{name} mode 0100755\n')
subprocess.run([sys.executable,str(repo/'port/scripts/check-phase4-frontend-audio-hooks.py'),str(stage)],check=True)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/muos-c06-session"
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[audit],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
assert sha(stage/'extracted'/name)==entry['sha256'] and not (stage/'extracted/var/lib/muos-seedrng').exists()
required={**m['unchanged_required'],**{n:sha(base/'extracted'/n) for n in ['usr/libexec/muos-c01-run','usr/share/muos-diagnostic/c06-control-tone.wav']}}
plan={'experiment':m['experiment'],'diagnostic_revision_update':3,'authorized_secondary_c06_revision':True,'installer_sha256':sha(repo/'port/scripts/install-phase4-service-diagnostic.py'),'entries':[entry],'unchanged_required':required}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inputs=['port/scripts/prepare-phase4-frontend-audio-native-effects.py','port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh','port/scripts/check-phase4-frontend-audio-hooks.py','port/scripts/install-phase4-service-diagnostic.py']
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'physical_native_effects_tested':False,'original_nav_confirm_back':True,'help_uses_confirm_control_only':True,'rate_reference_activity_retained':True,'gain_157_route_software_unchanged':True,'hook_fixtures':json.loads((stage/'hook-fixtures.json').read_text()),'port_inputs':{n:sha(repo/n) for n in inputs}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-frontend-native-effects').write_text(str(stage)+'\n')
print('C06 original nav effects audited:',stage)
