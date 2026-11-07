#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C06: combine verified C04 UI and C05 audio on the seedless host blueprint."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/audio-route.9tz8v3zh'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
assert not (base/'extracted/var/lib/muos-seedrng').exists()
stage=Path(tempfile.mkdtemp(prefix='frontend-audio.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
experiment='MUOS-R35S-FRONTEND-AUDIO-P4-C06'
bootstrap=(base/'extracted/sbin/muos-ext4-diag').read_text().replace('/etc/muos-audio-diagnostic','/etc/muos-frontend-audio-diagnostic').replace('MUOS-R35S-AUDIO-P4-C05',experiment).replace("'C05 marker missing'","'C06 marker missing'").replace('muOS C02: STOPPED','muOS C06: STOPPED').replace('C02: starting BusyBox init','C06: starting BusyBox init')
run=(base/'extracted/usr/libexec/muos-c01-run').read_text().replace('C05','C06').replace('c05','c06').replace('MUOS-R35S-AUDIO-P4-C06',experiment).replace('/etc/muos-audio-diagnostic','/etc/muos-frontend-audio-diagnostic').replace('DIAG07','DIAG08')
a=run.index('# SPDX-License-Identifier: MIT\n# Hook before S95');z=run.index('. /usr/libexec/muos-c01-chain',a)
run=run[:a]+'. /usr/libexec/muos-c06-session\n'+run[z:]
run=run.replace('c06_play > "$state/play.log"','c06_frontend > "$state/frontend.log"')
a=run.index("    echo 'AUDIO START'");z=run.index("    echo 'ACTIVE AUDIO GRAPH'",a)
run=run[:a]+'''    echo 'FRONTEND'; cat "$state/frontend.log" 2>/dev/null
    echo 'AUDIO START'
    for name in ui-during.txt ui-before-stop.txt; do
        echo "FILE=$name"; cat "$state/$name" 2>/dev/null
    done
'''+run[z:]
anchor="    echo 'FINAL STATUS';";assert run.count(anchor)==1
run=run.replace(anchor,'''    echo 'PERSISTENT CONFIG RESTORE'; cat "$state/persistent-restore.txt" 2>/dev/null
    echo 'CACHE RESTORED'; cat "$state/cache-restored.txt" 2>/dev/null
'''+anchor)
run=run.replace('C06: AUDIO / INPUT OK','C06: FRONTEND / AUDIO / INPUT OK').replace('Audio stopped. No frontend or network.','Frontend and audio stopped. No network.')
payload={'sbin/muos-ext4-diag':bootstrap,'usr/libexec/muos-c01-run':run,
 'usr/libexec/muos-c06-session':(repo/'port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh').read_text(),
 'etc/muos-frontend-audio-diagnostic':experiment+'\n'}
entries=[];commands=[]
for name,text in payload.items():
    p=assets/name.replace('/','_');p.write_text(text);old=base/'extracted'/name;mode=0o644 if name.startswith('etc/') else 0o755
    entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
    if old.exists():commands.append('rm /'+name)
    commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
subprocess.run([sys.executable,str(repo/'port/scripts/check-phase4-frontend-audio-hooks.py'),str(stage)],check=True)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for script in sbin/muos-ext4-diag usr/libexec/muos-c01-run usr/libexec/muos-c06-session; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$script"
done
for file in opt/muos/frontend/muxfrontend usr/libexec/muos-ui-supervisor usr/bin/amixer usr/bin/wpctl; do
 name=${file##*/}
 readelf -h -l -d "$root/$file" > "$name-elf.txt"
 qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --list "$root/$file" > "$name-loader.txt" 2>&1
done
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[audit],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
required=set(m['unchanged_required'])|{'usr/lib/libmali-bifrost-g31-rxp0-gbm.so','usr/lib/libSDL2-2.0.so.0.3000.12','usr/libexec/muos-ui-supervisor','etc/init.d/S99muos-ui','opt/muos/frontend/muxfrontend','usr/libexec/muos-drm-mode-probe','usr/libexec/muos-audio-functions'}
required|={'opt/muos/share/theme/MustardOS/sound/'+name+'.wav' for name in ['confirm','info_open','info_close']}
for name in required:assert sha(stage/'extracted'/name)==sha(base/'extracted'/name)
plan={'experiment':experiment,'authorized_secondary_c06_install':True,'installer_sha256':sha(repo/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':{name:sha(base/'extracted'/name) for name in sorted(required)}}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inputs=['port/scripts/prepare-phase4-native-frontend-audio.py','port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh','port/scripts/check-phase4-frontend-audio-hooks.py','port/scripts/install-phase4-service-diagnostic.py']
record={**plan,'scope':'90s supervised frontend, real PipeWire, SPK_HP/gain157/software unity; no hotkeys','base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,'hook_fixtures':json.loads((stage/'hook-fixtures.json').read_text()),'seed_material_included':False,'binaries_rebuilt':False,'native_frontend_audio_tested':False,'kernel_dtb_bootloader_partition_changed':False,'diagnostic_help_uses_confirm_wav_temporary_binds':True,'original_config_profile_help_preserved':True,'port_inputs':{name:sha(repo/name) for name in inputs}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(work/'linux-diagnostic/latest-native-frontend-audio').write_text(str(stage)+'\n')
print('C06 audited; native UI/audio pending:',stage)
