#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C47 parser/ELF and fixed-content launcher checks; no device access."""
from pathlib import Path
import json,os,subprocess,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'nes-core'
host=Path((area/'latest-host').read_text().strip());hr=json.loads((host/'analysis.json').read_text());assert hr['passed']
core=Path((area/'latest').read_text().strip());nr=json.loads((core/'analysis.json').read_text());api=Path((area/'latest-api').read_text().strip());ar=json.loads((api/'analysis.json').read_text());assert ar['passed'] and ar['build_stage']==str(core)
for r in [hr,nr,ar]:
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h
proof=repo/'dist/phase4/native-app-selection'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work));root='/work/rootfs-candidate/composition.w59vz7vo/target';src=rel(host/'source/retro/core')
code=f'''cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
for pair in startup:phase4-muxretro-startup-check deadline:phase4-retro-deadline-check content:phase4-content-deadline-check;do
 name=${{pair%%:*}};test=${{pair#*:}}
 "$cc" -O2 -mcpu=cortex-a35 -I{src} /port/diagnostics/$test.c {src}/startup.c {rel(host/'source/retro/netplay/address.c')} -o {rel(stage)}/$name
 qemu-aarch64 -cpu cortex-a35 -L {root} {rel(stage)}/$name
done
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(host/'source/bin/muxretro')} --version
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(host/'source/bin/muxretro')} --help
'''
(stage/'check.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('check.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr[-2500:]);assert 'C47_CONTENT_PARSER_OK cases=11' in r.stdout and 'C44_DEADLINE_CASES_OK=11' in r.stdout and 'cases=18' in r.stdout
launcher=repo/'port/device/rk-r35s-p0/nes-core/app-launch.sh';selector=repo/'port/device/rk-r35s-p0/nes-core/select.sh';screen=repo/'port/device/rk-r35s-p0/nes-core/stopped-screen.sh'
for p in [launcher,selector,screen]:subprocess.run(['sh','-n',str(p)],check=True)
cases=[]
for name in ['valid','tampered_ROM','missing_ROM','symlink_ROM','bad_manifest','persistent_fs','existing_content','symlink_ROMS']:
 d=stage/name;d.mkdir(mode=0o700);(d/'media').mkdir();(d/'core.so').write_bytes(b'fixture core, never executed');(d/'core.so').chmod(0o700)
 (d/'r35s-flight.nes').write_bytes((core/'r35s-flight.nes').read_bytes());(d/'r35s-flight.nes').chmod(0o700)
 (d/'nes-assets.sha256').write_text(sha(d/'core.so')+'  core.so\n'+sha(d/'r35s-flight.nes')+'  r35s-flight.nes\n');(d/'nes-assets.sha256').chmod(0o600)
 program=d/'muxretro';program.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > '+str(d/'argv')+'\n');program.chmod(0o700)
 if name=='tampered_ROM':(d/'r35s-flight.nes').write_bytes(b'bad')
 if name=='missing_ROM':(d/'r35s-flight.nes').unlink()
 if name=='symlink_ROM':(d/'r35s-flight.nes').unlink();(d/'r35s-flight.nes').symlink_to(d/'core.so')
 if name=='bad_manifest':(d/'nes-assets.sha256').write_text('0'*64+'  ../outside\n')
 if name=='existing_content':(d/'media/ROMS/NES').mkdir(parents=True);(d/'media/ROMS/NES/r35s-flight.nes').touch()
 if name=='symlink_ROMS':(d/'outside').mkdir();(d/'media/ROMS').symlink_to(d/'outside',target_is_directory=True)
 code=launcher.read_text().replace('/run/muos-prefs-data.??????',str(d)).replace('/mnt/mmc',str(d/'media')).replace('0:0:',f'{os.getuid()}:{os.getgid()}:')
 code='findmnt() { echo '+('ext4' if name=='persistent_fs' else 'tmpfs')+'; };\n'+code
 (d/'fixture.sh').write_text(code)
 r=subprocess.run(['sh',str(d/'fixture.sh'),str(d)],capture_output=True,text=True,timeout=10)
 (d/'stdout').write_text(r.stdout);(d/'stderr').write_text(r.stderr)
 assert (r.returncode==0)==(name=='valid'),(name,r.returncode,r.stdout,r.stderr)
 assert (d/'argv').exists()==(name=='valid')
 if name=='valid':assert (d/'argv').read_text().splitlines()==[str(d/'core.so'),str(d/'media/ROMS/NES/r35s-flight.nes'),'--fresh','--diagnostic-content','--diagnostic-seconds=30']
 cases.append(name)
report={'passed':True,'build_stage':str(host),'binary_sha256':hr['binary_sha256'],'core_build_stage':str(core),'api_stage':str(api),'parser_cases':18+11+11,'launcher_cases':cases,'C46_immutable_proof_verified':True,'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-content-deadline-check.c',launcher,selector,screen]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n');print('C47 parser/loader/launcher guards passed:',stage)
