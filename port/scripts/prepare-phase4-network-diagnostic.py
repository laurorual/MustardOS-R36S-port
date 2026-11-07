#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare a credentialless C07 host blueprint; no live card access."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/frontend-navigation-level.ed62uz58'
audit=Path((work/'network-tools/latest-audit').read_text().strip())
meta=json.loads((base/'manifest.json').read_text());tools=json.loads((audit/'report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert tools['passed'] and sha(base/'rootfs.ext4')==meta['rootfs_sha256']
assert 'usr/sbin/usb_modeswitch' in tools['new_files']
stage=Path(tempfile.mkdtemp(prefix='network.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
payload={}
for name,record in tools['new_files'].items():
    p=audit/'root'/name;assert sha(p)==record['sha256'];payload[name]=p.read_bytes()
source=repo/'port/device/rk-r35s-p0/network-diagnostic'
for target,name in [('network','network.sh'),('usb-mode','usb-mode.sh'),('dhcp','dhcp.sh'),('run','run.sh')]:
    payload['usr/libexec/muos-c07-'+target]=(source/name).read_bytes()
pub=(work/'private/c07-client.pub').read_text().strip()
assert pub.startswith('ssh-ed25519 ') and len(pub.split())==3
payload['etc/muos-network-authorized_key']=(pub+'\n').encode()
payload['etc/muos-network-diagnostic']=b'MUOS-R35S-NETWORK-P4-C07\n'
payload['usr/share/muos-diagnostic/c07-licenses.txt']='\n\n'.join(
    '=== '+str(p.relative_to(audit/'licenses'))+' ===\n'+p.read_text()
    for p in sorted((audit/'licenses').rglob('*')) if p.is_file()).encode()
tab=(base/'extracted/etc/inittab').read_text()
assert tab.count('/usr/libexec/muos-c01-run')==2
payload['etc/inittab']=tab.replace('/usr/libexec/muos-c01-run','/usr/libexec/muos-c07-run').encode()
bootstrap=(base/'extracted/sbin/muos-ext4-diag').read_text()
bootstrap=bootstrap.replace('C06','C07').replace('/etc/muos-frontend-audio-diagnostic','/etc/muos-network-diagnostic').replace('MUOS-R35S-FRONTEND-AUDIO-P4-C07','MUOS-R35S-NETWORK-P4-C07')
a=bootstrap.index('for usb in /sys/bus/usb/devices/*; do\n');z=bootstrap.index("printf '\\033",a)
bootstrap=bootstrap[:a]+'# C07 explicitly permits the dual-mode Realtek dongle.\n'+bootstrap[z:]
payload['sbin/muos-ext4-diag']=bootstrap.encode()
entries=[];commands=[]
for name,data in payload.items():
    asset=assets/name.replace('/','_');asset.write_bytes(data);old=base/'extracted'/name
    mode=0o755 if name.startswith(('usr/sbin/','usr/bin/','usr/lib/','usr/libexec/','sbin/')) else 0o644
    entries.append({'path':name,'asset':asset.name,'sha256':sha(asset),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
    if old.exists():commands.append('rm /'+name)
    commands += [f'write assets/{asset.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
code=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for name in sbin/muos-ext4-diag usr/libexec/muos-c07-network usr/libexec/muos-c07-usb-mode usr/libexec/muos-c07-dhcp usr/libexec/muos-c07-run; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$name"
done
if qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh "$root/sbin/muos-ext4-diag" > bootstrap-pid-guard.txt 2>&1; then exit 1; else test "$?" = 64; fi
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[code],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
assert not (stage/'extracted/var/lib/muos-network').exists()
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
required={name:value for name,value in meta['unchanged_required'].items() if name not in payload}
required['usr/libexec/muos-c01-run']=sha(base/'extracted/usr/libexec/muos-c01-run')
required['usr/libexec/muos-c06-session']=sha(base/'extracted/usr/libexec/muos-c06-session')
for name in tools['existing_libraries_verified']:
    for folder in ['lib','usr/lib']:
        p=base/'extracted'/folder/name
        if p.exists():
            p=p.resolve();assert p.is_relative_to(base/'extracted')
            required[str(p.relative_to(base/'extracted'))]=sha(p);break
for name,expected in required.items():assert sha(stage/'extracted'/name)==expected
plan={'experiment':'MUOS-R35S-NETWORK-P4-C07','authorized_secondary_c07_install':True,
      'installer_sha256':sha(repo/'port/scripts/install-phase4-network-diagnostic.py'),
      'entries':entries,'unchanged_required':required}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'host_audit_passed':True,'rootfs_sha256':sha(stage/'rootfs.ext4'),
        'base_manifest_sha256':sha(base/'manifest.json'),'tools_report_sha256':sha(audit/'report.json'),
        'credentials_or_seed_included':False,'wifi_dhcp_ssh_physical_tested':False,
        'original_c06_runner_preserved':True,'sources':{str(p.relative_to(repo)):sha(p) for p in source.glob('*.sh')}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(work/'linux-diagnostic/latest-network').write_text(str(stage)+'\n')
print('C07 credentialless blueprint audited:',stage)
