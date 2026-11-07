#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C07r2: targeted retained-c820 USB reset/reprobe; no new binary or private data."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/network-deadline.6qfz33xd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
fixtures=Path((work/'network-tools/latest-hooks').read_text().strip());checks=json.loads((fixtures/'report.json').read_text())
assert checks['passed'] and len(checks['cases'])==20 and checks['stage_limits']['usb-mode']=='120'
stage=Path(tempfile.mkdtemp(prefix='network-reprobe.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
entries=[];commands=[]
for target,source in [('usr/libexec/muos-c07-usb-mode','usb-mode.sh'),('usr/libexec/muos-c07-network','network.sh'),('usr/libexec/muos-c07-run','run.sh')]:
    p=assets/target.replace('/','_');shutil.copyfile(repo/'port/device/rk-r35s-p0/network-diagnostic'/source,p)
    entries.append({'path':target,'asset':p.name,'sha256':sha(p),'old_sha256':sha(base/'extracted'/target),'mode':0o755})
    commands += [f'rm /{target}',f'write assets/{p.name} /{target}',f'set_inode_field /{target} mode 0100755']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
code=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for p in usr/libexec/muos-c07-network usr/libexec/muos-c07-usb-mode usr/libexec/muos-c07-run; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$p"
done
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[code],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
assert not (stage/'extracted/var/lib/muos-network').exists()
changed={e['path'] for e in entries}
unchanged={k:v for k,v in m['unchanged_required'].items() if k not in changed}
unchanged.update({e['path']:e['sha256'] for e in m['entries'] if e['path'] not in changed})
for name,expected in unchanged.items():assert sha(stage/'extracted'/name)==expected
plan={'experiment':m['experiment'],'authorized_secondary_c07_revision':True,'diagnostic_revision_update':2,
 'installer_sha256':sha(repo/'port/scripts/install-phase4-network-diagnostic.py'),'entries':entries,'unchanged_required':unchanged}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,
 'hook_fixtures':checks,'hook_report_sha256':sha(fixtures/'report.json'),'private_material_included':False,'native_reset_reprobe_tested':False,
 'underlying_retained_state_root_cause_unproven':True,'binaries_kernel_dtb_bootloader_unchanged':True,
 'sources':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/check-phase4-network-hooks.py',*[repo/'port/device/rk-r35s-p0/network-diagnostic'/n for n in ['usb-mode.sh','network.sh','run.sh']]]}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(work/'linux-diagnostic/latest-network-reprobe').write_text(str(stage)+'\n')
print('C07r2 reset/reprobe host blueprint audited:',stage)
