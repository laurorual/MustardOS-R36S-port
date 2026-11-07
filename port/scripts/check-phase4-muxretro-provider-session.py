#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C68 binding and fixed RAM-host dispatcher checks; no core/ROM execution."""
from pathlib import Path
import ast, copy, json, subprocess, tempfile
from phase4_candidate import sha
from phase4_muxretro_provider_session import historical, bind, render_online, AREA, NATIVE, WORK, REPO, C66, C67, watch_script

ctx, prior_stage, prior, provider_stage, provider, online = historical()
AREA.mkdir(exist_ok=True)
for p in NATIVE.glob('*.sh'):
    subprocess.run(['sh', '-n', str(p)], check=True)
ast.parse(render_online(online))
watch = watch_script('/run/muos-prefs-data.ABC123')
assert '= /opt/muos/frontend/muxretro ]' not in watch and '/host/muxretro ]' in watch
subprocess.run(['sh', '-n'], input=watch, text=True, check=True)
r66 = ctx['C66_report']
obs = {'passed': True, 'experiment': 'C68_OBSERVED_BOOT', 'boot_sequence': r66['boot_sequence'],
       'kernel_boot_id': r66['kernel_boot_id'], 'prior_analysis_sha256': sha(prior_stage / 'analysis.json'),
       'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),
       'C66_analysis_sha256': sha(C66 / 'analysis.json'), 'C67_analysis_sha256': sha(C67 / 'analysis.json'),
       'root_RO_installed_payload_and_foundation_verified': True, 'infrastructure': 'fixture', 'agent_requested_reboot': False}
assert bind(prior, provider, obs, r66['boot_sequence'], r66['kernel_boot_id']) == r66['libraries']
cases = ['valid-C66-exact-boot-and-C67-receipt', 'rendered-source-and-map-watcher-syntax']
mutations = [
 ('new-boot-refused', lambda o, a: (o.update(boot_sequence=a['boot']+1), a.update(boot=a['boot']+1))),
 ('bool-boot', lambda o, a: a.update(boot=True)),
 ('UUID-drift', lambda o, a: a.update(uuid='00000000-0000-0000-0000-000000000000')),
 ('C66-receipt-drift', lambda o, a: o.update(C66_analysis_sha256='00'*32)),
 ('C67-receipt-drift', lambda o, a: o.update(C67_analysis_sha256='00'*32)),
 ('old-observation-role', lambda o, a: o.update(experiment='C66_OBSERVED_BOOT')),
 ('unverified-root', lambda o, a: o.update(root_RO_installed_payload_and_foundation_verified=False)),
 ('bool-observed-boot', lambda o, a: o.update(boot_sequence=True)),
 ('empty-infra', lambda o, a: o.update(infrastructure=''))]
for label, mutate in mutations:
    o = copy.deepcopy(obs)
    a = {'boot': r66['boot_sequence'], 'uuid': r66['kernel_boot_id']}
    mutate(o, a)
    try: bind(prior, provider, o, a['boot'], a['uuid'])
    except AssertionError: pass
    else: raise AssertionError(label)
    cases.append(label)
stage = Path(tempfile.mkdtemp(prefix='checks.', dir=AREA))
fixture = r'''
from pathlib import Path
import os,shutil,json,subprocess
source=Path('/port/device/rk-r35s-p0/muxretro-provider-session/installed-host.sh').read_text()
assert source.count('root=/\n')==1
source=source.replace('root=/\n','root=/tmp/c68-root\n').replace('/mnt/mmc','/tmp/c68-content')
anchor='exec "$capsule/host/muxretro" "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit'
assert source.count(anchor)==1
source=source.replace(anchor,anchor.replace('exec ',''' + '"""' + r'''printf '%s\n' ''' + '"""' + r''')+' > /tmp/c68-exec')
Path('/tmp/c68-guard.sh').write_text(source)
root=Path('/tmp/c68-root');cap=Path('/run/muos-prefs-data.ABC123');content=Path('/tmp/c68-content/ROMS/GB/private.gb')
old=Path('/work/muxretro-package/build.mdou4mqr/target')
rows=json.loads(Path('/work/muxretro-install/install.67io22z3/plan.json').read_text())['files']
provider=Path('/work/frontend-libs/build.84o1r4aj/target/opt/muos/frontend/lib')
host=Path('/work/muxretro-provider/build.f9a1ac69/target/opt/muos/frontend/muxretro')
def reset():
 for p in [root,cap,content.parents[2]]:
  if p.exists():shutil.rmtree(p)
 Path('/tmp/c68-exec').unlink(missing_ok=True)
 root.mkdir(mode=0o755);cap.mkdir(mode=0o700)
 for row in rows:
  p=root/row['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/row['path'],p);p.chmod(row['mode'])
 for name in ['lib','provider-lib','host']:(cap/name).mkdir(mode=0o700)
 for n in ['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so']:
  shutil.copyfile(provider/n,cap/'provider-lib'/n);(cap/'provider-lib'/n).chmod(0o700)
  if n!='libmuxmod.so':
   shutil.copyfile(provider/n,cap/'lib'/n);(cap/'lib'/n).chmod(0o700)
 shutil.copyfile(host,cap/'host/muxretro');(cap/'host/muxretro').chmod(0o700)
 shutil.copyfile('/port/device/rk-r35s-p0/muxretro-provider-session/frontend-libs.sh',cap/'frontend-libs.sh')
 (cap/'role').write_text('load\n');(cap/'role').chmod(0o600)
 for n in ['core.so','private.gb']:(cap/n).write_bytes(b'C68 synthetic content');(cap/n).chmod(0o700)
 content.parent.mkdir(parents=True);content.write_bytes((cap/'private.gb').read_bytes());content.chmod(0o400)
def call(label,ok=False,operation='launch',ld=None):
 code='findmnt() { case "$*" in *OPTIONS*) echo ro;;*FSTYPE*) echo tmpfs;;*) return 99;;esac; }\n'
 code+='set -- '+str(cap)+' '+operation+'\n. /tmp/c68-guard.sh\n'
 env={**os.environ,'LD_BIND_NOW':'1','LD_LIBRARY_PATH':str(cap)+'/provider-lib:/opt/muos/frontend/lib'}
 if ld is not None:env['LD_LIBRARY_PATH']=ld
 r=subprocess.run(['sh','-c',code],capture_output=True,text=True,env=env,timeout=10)
 assert (r.returncode==0)==ok,(label,r.returncode,r.stdout,r.stderr)
 assert Path('/tmp/c68-exec').exists()==(ok and operation=='launch'),label
 if ok and operation=='launch':
  assert Path('/tmp/c68-exec').read_text().splitlines()==[str(cap/'host/muxretro'),str(cap/'core.so'),str(content),'--fresh','--diagnostic-content','--diagnostic-seconds=45','--diagnostic-hotkey-exit']
 print('C68_PASS_'+label)
reset();call('valid-fixed-RAM-launch',True)
reset();call('valid-check-no-execution',True,'check')
reset();(cap/'host/muxretro').unlink();call('missing-RAM-host-no-installed-fallback')
reset();shutil.copyfile(old/'opt/muos/frontend/muxretro',cap/'host/muxretro');call('old-host-bytes-refused')
reset();p=cap/'host/muxretro';p.write_bytes(p.read_bytes()+b'bad');call('corrupt-host')
reset();(cap/'host/muxretro').chmod(0o755);call('wrong-host-mode')
reset();(cap/'host/muxretro').unlink();(cap/'host/muxretro').symlink_to(host);call('symlink-host')
reset();os.link(cap/'host/muxretro',cap/'other');call('host-extra-link')
reset();(cap/'host').chmod(0o755);call('host-dir-mode')
reset();shutil.move(cap/'host',cap/'original');(cap/'host').symlink_to(cap/'original');call('host-dir-symlink')
reset();(root/'opt/muos/frontend/muxretro').unlink();call('installed-package-still-required')
reset();(cap/'muxretro').write_text('fallback');call('root-capsule-fallback-forbidden')
reset();(cap/'role').write_text('save\n');call('writer-role-forbidden')
reset();call('unknown-operation',operation='other')
reset();call('extra-argument',operation='launch ignored')
reset();call('wrong-environment',ld='/opt/muos/frontend/lib')
reset();p=cap/'provider-lib/libmuxcom.so';p.write_bytes(p.read_bytes()+b'bad');call('provider-corrupt')
'''
(stage / 'fixtures.py').write_text(fixture)
ast.parse(fixture)
container = (WORK / 'rootfs-container.iid').read_text().strip()
cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all', '--security-opt=no-new-privileges',
       '--userns=keep-id:uid=0,gid=0', '--user=0', '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m',
       '--tmpfs', '/run:rw,nosuid,nodev,size=128m', '-v', f'{WORK}:/work:ro,z', '-v', f'{REPO}/port:/port:ro,z',
       container, 'python3', '/work/' + str((stage / 'fixtures.py').relative_to(WORK))]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
    (stage / ('fixtures.' + suffix)).write_text(value)
assert r.returncode == 0, (stage, r.stdout[-1000:], r.stderr[-2000:])
shell_cases = [line for line in r.stdout.splitlines() if line.startswith('C68_PASS_')]
sources = [Path(__file__), REPO / 'port/scripts/phase4_muxretro_provider_session.py',
           REPO / 'port/scripts/prepare-phase4-muxretro-provider-session.py', REPO / 'port/scripts/run-phase4-muxretro-provider-session.py',
           *NATIVE.glob('*.sh')]
report = {'passed': True, 'experiment': 'C68_RAM_HOST_CHECKS', 'binding_cases': cases, 'dispatcher_cases': shell_cases,
          'case_count': len(cases) + len(shell_cases), 'C66_checks_reused': 66, 'device_accessed': False,
          'core_or_ROM_executed': False, 'source_sha256': {str(p.relative_to(REPO)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(AREA / 'latest-checks').write_text(str(stage) + '\n')
print('C68 fixed RAM host checks passed:', report['case_count'], stage)
