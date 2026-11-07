#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C63 installed-path refusals and explicit C61/C62 binding, without hardware."""
from pathlib import Path
import ast,copy,json,subprocess,tempfile
from phase4_candidate import sha,sums
from phase4_installed_host_session import bind_installed_host
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'installed-host-session';area.mkdir(exist_ok=True)
for name in ['muxretro-installed','muxretro-package-session']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
renderer=repo/'port/scripts/prepare-phase4-installed-host-session.py'
runner=repo/'port/scripts/run-phase4-installed-host-session.py';analyzer=repo/'port/scripts/analyze-phase4-installed-host-session.py'
before={p:p.read_bytes() for p in [runner,analyzer]}
subprocess.run(['python3',str(renderer)],check=True,capture_output=True)
for p,v in before.items():assert p.read_bytes()==v;ast.parse(p.read_text())
text=runner.read_text()
assert text.index("del files['muxretro']")<text.index('for n,f in files.items():\n r=subprocess.run')
assert "assert 'muxretro' not in files and 'save-store' not in files" in text
native=repo/'port/device/rk-r35s-p0/installed-host-session'
old=(repo/'port/device/rk-r35s-p0/gb-persist/app-launch.sh').read_text()
anchor='exec "$capsule/muxretro" "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit'
assert (native/'app-launch.sh').read_text()==old.replace(anchor,'exec /bin/sh "$capsule/installed-host.sh" "$capsule" launch')
guard=(native/'installed-host.sh').read_text();assert '"$capsule/muxretro"' not in guard
assert guard.count('root=/\n')==1
for p in native.glob('*.sh'):subprocess.run(['sh','-n',str(p)],check=True)
prior=json.loads((work/'muxretro-package-session/load.upr3y148/analysis.json').read_text())
deployment=work/'muxretro-install/install.67io22z3'
d=json.loads((deployment/'install-analysis.json').read_text());plan=json.loads((deployment/'plan.json').read_text())
assets={k:prior[k] for k in ['host_binary_sha256','core_sha256','ROM_sha256','runner_sha256','worker_sha256','library_sha256','cycle_sha256','state_inspector_sha256','save_store_binary_sha256']}
args=dict(boot=prior['boot_sequence'],uuid=prior['kernel_boot_id'],identity=prior['private_identity'],assets=assets,plan_sha=sha(deployment/'plan.json'))
def invoke(p,d,pl,a):return bind_installed_host(p,d,pl,a['boot'],a['uuid'],a['identity'],a['assets'],a['plan_sha'])
assert invoke(prior,d,plan,args)==assets['host_binary_sha256'];cases=['C61-C62-same-boot-installed-host']
mutations=[('boot-changed',lambda p,d,pl,a:a.update(boot=a['boot']+1)),('bool-boot',lambda p,d,pl,a:a.update(boot=True)),
 ('UUID-changed',lambda p,d,pl,a:a.update(uuid='wrong')),('wrong-identity',lambda p,d,pl,a:a.update(identity='wrong')),
 ('plan-receipt-drift',lambda p,d,pl,a:a.update(plan_sha='00'*32)),
 ('writer-role',lambda p,d,pl,a:p.update(mode='save')),('failed-outcome',lambda p,d,pl,a:p.update(outcome='failed')),
 ('different-deployment-boot',lambda p,d,pl,a:d.update(boot_sequence=69)),
 ('replaced-existing',lambda p,d,pl,a:d.update(existing_files_replaced=1)),
 ('automatic-activation',lambda p,d,pl,a:pl['runtime_contract'].update(activation='automatic')),
 ('wrong-C46-library',lambda p,d,pl,a:pl['runtime_contract'].update(GUI_requires_C46_RAM_libmuxmod_sha256='00'*32)),
 ('wrong-host-mode',lambda p,d,pl,a:pl['files'][0].update(mode=0o644)),
 ('host-hash-drift',lambda p,d,pl,a:pl['files'][0].update(sha256='00'*32)),
 ('neighbor-host-path',lambda p,d,pl,a:pl['files'][0].update(path='opt/muos/frontend/neighbor'))]
for k in ['passed','cleanup_passed','RAM_removed','root_ro','global_mountinfo_unchanged','store_matches_previous_boot','installed_CLI_used','native_ABI_passed','exact_C59_boot_retained']:
 mutations.append(('prior-'+k,lambda p,d,pl,a,k=k:p.update({k:False})))
for k in ['passed','root_read_only','infrastructure_unchanged','private_state_fingerprint_matched','installed_ABI_tested','RAM_removed','global_mounts_unchanged']:
 mutations.append(('deployment-'+k,lambda p,d,pl,a,k=k:d.update({k:False})))
for k in ['reboot_requested','token_or_service_enabled','p3_mounted','GUI_replayed','runtime_C46_override_installed']:
 mutations.append(('deployment-'+k,lambda p,d,pl,a,k=k:d.update({k:True})))
for k in assets:
 mutations.append(('asset-'+k,lambda p,d,pl,a,k=k:a['assets'].update({k:'00'*32})))
for label,mutate in mutations:
 p,dr,pl,a=map(copy.deepcopy,[prior,d,plan,args]);mutate(p,dr,pl,a)
 try:invoke(p,dr,pl,a)
 except AssertionError:pass
 else:raise AssertionError(label)
 cases.append(label)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
# Only filesystem checks are emulated. The final fixed exec is recorded, not
# executed; no core, commercial ROM, UI or service is involved in these cases.
fixture=r'''
from pathlib import Path
import json,os,shutil,subprocess
source=Path('/port/device/rk-r35s-p0/installed-host-session/installed-host.sh').read_text()
assert source.count('root=/\n')==1
source=source.replace('root=/\n','root=/tmp/c63-root\n').replace('/mnt/mmc','/tmp/c63-content')
target='exec /opt/muos/frontend/muxretro "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit'
assert source.count(target)==1
source=source.replace(target,''' + '"""' + r'''printf '%s\n' /opt/muos/frontend/muxretro "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit > /tmp/c63-exec
exit 0''' + '"""' + r''')
Path('/tmp/c63-guard.sh').write_text(source)
root=Path('/tmp/c63-root');capsule=Path('/run/muos-prefs-data.ABC123');content=Path('/tmp/c63-content/ROMS/GB/private.gb')
build=Path(os.environ['PACKAGE_TARGET']);rows=json.loads(Path(os.environ['PLAN']).read_text())['files']
def reset():
 for path in [root,capsule,content.parents[2]]:
  if path.exists():shutil.rmtree(path)
 Path('/tmp/c63-exec').unlink(missing_ok=True)
 root.mkdir(mode=0o755);capsule.mkdir(mode=0o700);content.parent.mkdir(parents=True)
 for r in rows:
  dest=root/r['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(build/r['path'],dest);dest.chmod(r['mode'])
 (capsule/'role').write_text('load\n');(capsule/'role').chmod(0o600)
 for n in ['core.so','private.gb']:(capsule/n).write_bytes(b'C63 synthetic bytes');(capsule/n).chmod(0o700)
 content.write_bytes((capsule/'private.gb').read_bytes());content.chmod(0o400)
def call(label,ok=False,operation='launch',options='ro',fstype='tmpfs',busybox=False):
 stub=''' + '"""' + r'''findmnt() { case "$*" in *OPTIONS*) printf '%s\n' "$C63_OPTIONS";;*FSTYPE*) printf '%s\n' "$C63_FS";;*) return 99;;esac; }
''' + '"""' + r'''
 if busybox:stub+='dirname() { qemu-aarch64 -cpu cortex-a35 -L "$SYSROOT" "$SYSROOT/bin/busybox" dirname "$1"; }\n'
 stub+='set -- /run/muos-prefs-data.ABC123 '+operation+'\n. /tmp/c63-guard.sh\n'
 r=subprocess.run(['sh','-c',stub],env={**os.environ,'C63_OPTIONS':options,'C63_FS':fstype},capture_output=True,text=True,timeout=20)
 assert (r.returncode==0)==ok,(label,r.returncode,r.stdout,r.stderr)
 assert Path('/tmp/c63-exec').exists()==(ok and operation=='launch'),label
 if ok and operation=='launch':assert Path('/tmp/c63-exec').read_text().splitlines()==['/opt/muos/frontend/muxretro',str(capsule/'core.so'),str(content),'--fresh','--diagnostic-content','--diagnostic-seconds=45','--diagnostic-hotkey-exit']
 print('C63_PASS_'+label,flush=True)
reset();call('valid-check-no-content-execution',True,'check')
reset();call('valid-fixed-launch',True)
reset();call('native-BusyBox-parent-walk',True,'check',busybox=True)
for row in rows:
 path=root/row['path'];label=row['path'].replace('/','_')
 reset();path.write_bytes(path.read_bytes()+b'corrupt');call('hash-'+label)
 reset();path.chmod(0o600);call('mode-'+label)
 reset();path.unlink();path.symlink_to('/tmp');call('symlink-'+label)
reset();(root/'opt/muos/frontend/muxretro').unlink();call('installed-host-absent')
reset();os.link(root/'opt/muos/frontend/muxretro',root/'alias');call('installed-host-extra-link')
reset();(root/'opt/muos/frontend').chmod(0o777);call('wrong-parent-mode')
reset();shutil.move(root/'opt/muos/frontend',root/'opt/muos/original');(root/'opt/muos/frontend').symlink_to(root/'opt/muos/original');call('parent-symlink')
reset();(capsule/'muxretro').write_text('fallback');call('RAM-host-forbidden')
reset();(capsule/'muxretro').symlink_to('/nonexistent');call('RAM-host-dangling-link-forbidden')
reset();(capsule/'save-store').write_text('fallback');call('RAM-store-forbidden')
reset();(capsule/'role').write_text('save\n');call('writer-role-forbidden')
reset();(capsule/'role').chmod(0o644);call('wrong-role-mode')
reset();call('unknown-operation',operation='other')
reset();call('extra-argument',operation='launch ignored')
reset();call('root-RW',options='rw')
reset();call('capsule-not-tmpfs',fstype='ext4')
reset();content.chmod(0o600);content.write_bytes(b'different');content.chmod(0o400);call('content-mismatch')
reset();content.chmod(0o600);call('content-mode')
reset();content.unlink();content.symlink_to(capsule/'private.gb');call('content-symlink')
reset();(capsule/'core.so').unlink();call('core-absent')
'''
(stage/'fixtures.py').write_text(fixture)
container=(work/'rootfs-container.iid').read_text().strip();rel=lambda p:'/work/'+str(p.relative_to(work))
package=work/'muxretro-package/build.mdou4mqr/target'
command=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--tmpfs','/run:rw,nosuid,nodev,size=16m',
 '-v',f'{work}:/work:ro,z','-v',f'{repo}/port:/port:ro,z','-e','PACKAGE_TARGET='+rel(package),'-e','PLAN='+rel(deployment/'plan.json'),
 '-e','SYSROOT=/work/save-store-image/image.nlnmgzzb/target',container,'python3',rel(stage/'fixtures.py')]
r=subprocess.run(command,capture_output=True,text=True,timeout=120)
for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('fixtures.'+ext)).write_text(v)
assert r.returncode==0,(stage,r.stdout[-1000:],r.stderr[-2000:])
shell_cases=[s for s in r.stdout.splitlines() if s.startswith('C63_PASS_')]
sources=[Path(__file__),renderer,runner,analyzer,repo/'port/scripts/phase4_installed_host_session.py',*native.glob('*.sh')]
report={'passed':True,'experiment':'C63_INSTALLED_HOST_CHECKS','binding_cases':len(cases),'cases':cases,
 'dispatcher_cases':len(shell_cases),'dispatcher_case_names':shell_cases,'case_count':len(cases)+len(shell_cases),
 'device_accessed':False,'private_ROM_used':False,'host_or_core_executed':False,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C63 binding/fixed installed dispatcher checks passed:',report['case_count'],stage)
