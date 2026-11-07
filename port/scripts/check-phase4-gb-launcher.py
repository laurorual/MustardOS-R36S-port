#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C47 parser/ELF and fixed-content launcher checks; no device access."""
from pathlib import Path
import json,os,subprocess,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-core'
host=Path((work/'nes-core/latest-host').read_text().strip());hr=json.loads((host/'analysis.json').read_text());assert hr['passed']
core=Path((area/'latest').read_text().strip());nr=json.loads((core/'analysis.json').read_text());api=Path((area/'latest-api').read_text().strip());ar=json.loads((api/'analysis.json').read_text());assert ar['passed'] and ar['build_stage']==str(core)
for r in [hr,nr,ar]:
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
launcher=repo/'port/device/rk-r35s-p0/gb-core/app-launch.sh';selector=repo/'port/device/rk-r35s-p0/gb-core/select.sh';screen=repo/'port/device/rk-r35s-p0/gb-core/stopped-screen.sh';session=repo/'port/device/rk-r35s-p0/gb-core/session.sh'
for f in [launcher,selector,screen,session]:subprocess.run(['sh','-n',str(f)],check=True)
old=(repo/'port/device/rk-r35s-p0/nes-core/select.sh').read_text();a=old.index('if [ "$mode" = cycle ];then');b=old.index('mkdir -m 700 "$capsule/dispatch-owner"',a)
expected=(old[:a]+old[b:]).replace('cycle|observe','observe').replace('"$capsule/runner" 50','"$capsule/runner" 65').replace('seconds=30','seconds=45')
assert selector.read_text()==expected
cases=[]
for name in ['valid','tampered_ROM','missing_ROM','symlink_ROM','bad_manifest','persistent_fs','existing_content','symlink_ROMS']:
 d=stage/name;d.mkdir(mode=0o700);(d/'media').mkdir();(d/'core.so').write_bytes(b'fixture core, never executed');(d/'core.so').chmod(0o700)
 (d/'private.gb').write_bytes(b'synthetic guard input, never emulated');(d/'private.gb').chmod(0o700)
 (d/'gb-assets.sha256').write_text(sha(d/'core.so')+'  core.so\n'+sha(d/'private.gb')+'  private.gb\n');(d/'gb-assets.sha256').chmod(0o600)
 program=d/'muxretro';program.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > '+str(d/'argv')+'\n');program.chmod(0o700)
 if name=='tampered_ROM':(d/'private.gb').write_bytes(b'bad')
 if name=='missing_ROM':(d/'private.gb').unlink()
 if name=='symlink_ROM':(d/'private.gb').unlink();(d/'private.gb').symlink_to(d/'core.so')
 if name=='bad_manifest':(d/'gb-assets.sha256').write_text('0'*64+'  ../outside\n')
 if name=='existing_content':(d/'media/ROMS/GB').mkdir(parents=True);(d/'media/ROMS/GB/private.gb').touch()
 if name=='symlink_ROMS':(d/'outside').mkdir();(d/'media/ROMS').symlink_to(d/'outside',target_is_directory=True)
 code=launcher.read_text().replace('/run/muos-prefs-data.??????',str(d)).replace('/mnt/mmc',str(d/'media')).replace('0:0:',f'{os.getuid()}:{os.getgid()}:')
 code='findmnt() { echo '+('ext4' if name=='persistent_fs' else 'tmpfs')+'; };\n'+code
 (d/'fixture.sh').write_text(code)
 r=subprocess.run(['sh',str(d/'fixture.sh'),str(d)],capture_output=True,text=True,timeout=10)
 (d/'stdout').write_text(r.stdout);(d/'stderr').write_text(r.stderr)
 assert (r.returncode==0)==(name=='valid'),(name,r.returncode,r.stdout,r.stderr)
 assert (d/'argv').exists()==(name=='valid')
 if name=='valid':assert (d/'argv').read_text().splitlines()==[str(d/'core.so'),str(d/'media/ROMS/GB/private.gb'),'--fresh','--diagnostic-content','--diagnostic-seconds=45']
 cases.append(name)
report={'passed':True,'build_stage':str(host),'binary_sha256':hr['binary_sha256'],'core_build_stage':str(core),'api_stage':str(api),'parser_cases_reused':40,'launcher_cases':cases,'C47_selector_normalized_exact':True,'private_ROM_used_in_fixtures':False,'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),launcher,selector,screen,session]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n');print('C49 GB launcher guards passed:',stage)
