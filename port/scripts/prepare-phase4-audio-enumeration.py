#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 RK817 card path identity: apply the existing narrow WirePlumber profile."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
r=Path(__file__).resolve().parents[2];w=r/'build/phase4';base=w/'linux-diagnostic/audio-correct.c7dcno0u'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
s=Path(tempfile.mkdtemp(prefix='audio-enumerate.',dir=w/'linux-diagnostic'));a=s/'assets';a.mkdir();shutil.copyfile(base/'rootfs.ext4',s/'rootfs.ext4')
run=(base/'assets/usr_libexec_muos-c01-run').read_text();anchor='''    /usr/libexec/muos-audio-probe''';assert anchor in run
run=run.replace(anchor,'''    /usr/libexec/muos-run-bounded 5 pw-dump > "$state/pw-active.json" || return 1
'''+anchor)
anchor="    echo 'CORE FAILURE GRAPH'";assert anchor in run
run=run.replace(anchor,'''    echo 'ACTIVE AUDIO GRAPH'; head -c 196608 "$state/pw-active.json" 2>/dev/null
    echo
'''+anchor)
(a/'usr_libexec_muos-c01-run').write_text(run)
rule='usr/lib/udev/rules.d/79-muos-rk817-path.rules';shutil.copyfile(r/'port/device/rk-r35s-p0/audio-diagnostic/79-muos-rk817-path.rules',a/rule.replace('/','_'))
names=[rule,'usr/libexec/muos-c01-run'];entries=[];commands=[]
for name in names:
 p=a/name.replace('/','_');old=base/'extracted'/name;mode=0o644 if name==rule else 0o755
 entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
 if old.exists():commands.append('rm /'+name)
 commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
(s/'debugfs.commands').write_text('\n'.join(commands)+'\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{w}:/work:rw,z','-e','STAGE_REL='+str(s.relative_to(w)),(w/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/muos-c01-run"
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/bin/udevadm" test-builtin --help > path-id-help.txt 2>&1
'''
with (s/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(s/'extracted'/e['path'])==e['sha256']
assert 'path_id' in (s/'path-id-help.txt').read_text() and not (s/'extracted/var/lib/muos-seedrng').exists()
plan={'experiment':m['experiment'],'diagnostic_revision_update':3,'authorized_secondary_c05_revision':True,'installer_sha256':sha(r/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':m['unchanged_required']}
(s/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(s/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'native_audio_tested':False,'scope':'RK817 platform card imports native path_id; existing device/sink profile names unchanged; collect live graph','port_inputs':{n:sha(r/n) for n in ['port/scripts/prepare-phase4-audio-enumeration.py','port/device/rk-r35s-p0/audio-diagnostic/79-muos-rk817-path.rules','port/scripts/install-phase4-service-diagnostic.py']}}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(w/'linux-diagnostic/latest-audio-enumeration').write_text(str(s)+'\n');print('C05 RK817 path-id rule audited:',s)
