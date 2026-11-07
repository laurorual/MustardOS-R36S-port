#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C73 installed31 dispatcher checks; record exec, never run core or content."""
from pathlib import Path
import ast, copy, json, subprocess, tempfile
from phase4_candidate import sha
from phase4_installed_provider_session import historical, installed, bind, render_online, watch_script, AREA, NATIVE, WORK, REPO, proof, C72

ctx, prior_stage, prior, provider_stage, provider, online = historical()
AREA.mkdir(exist_ok=True)
for p in NATIVE.glob('*.sh'): subprocess.run(['sh', '-n', str(p)], check=True)
ast.parse(render_online(online))
watch = watch_script('/run/muos-prefs-data.ABC123')
assert '= /opt/muos/frontend/muxretro ]' in watch and '/host/muxretro ]' not in watch
assert all("grep -Fq '/opt/muos/frontend/lib/" + n in watch for n in ctx['C66_report']['libraries'])
subprocess.run(['sh', '-n'], input=watch, text=True, check=True)
r66 = ctx['C66_report']
obs = {'passed': True, 'experiment': 'C73_OBSERVED_BOOT', 'boot_sequence': r66['boot_sequence'],
       'kernel_boot_id': r66['kernel_boot_id'], 'prior_analysis_sha256': sha(prior_stage / 'analysis.json'),
       'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),
       'C66_analysis_sha256': sha(WORK / 'frontend-libs-session/load.o2agwm0q/analysis.json'),
       'C67_analysis_sha256': sha(ctx['C67_stage'] / 'analysis.json'),
       'C72_analysis_sha256': sha(C72 / 'install-analysis.json'),
       'root_RO_installed_payload_and_foundation_verified': True, 'infrastructure': 'fixture', 'agent_requested_reboot': False}
assert bind(prior, provider, obs, r66['boot_sequence'], r66['kernel_boot_id']) == r66['libraries']
cases = ['exact-C72-binding', 'installed-host-and-provider-map-syntax']
for key, value in [('experiment', 'C68_OBSERVED_BOOT'), ('boot_sequence', True),
                   ('C72_analysis_sha256', '00'*32), ('C66_analysis_sha256', '00'*32),
                   ('C67_analysis_sha256', '00'*32), ('infrastructure', ''),
                   ('root_RO_installed_payload_and_foundation_verified', False)]:
    changed = copy.deepcopy(obs);changed[key] = value
    try: bind(prior, provider, changed, r66['boot_sequence'], r66['kernel_boot_id'])
    except AssertionError: pass
    else: raise AssertionError(key)
    cases.append('reject-' + key)
for boot, uuid in [(r66['boot_sequence']+1, r66['kernel_boot_id']), (True, r66['kernel_boot_id']),
                   (r66['boot_sequence'], '00000000-0000-0000-0000-000000000000')]:
    try: bind(prior, provider, obs, boot, uuid)
    except AssertionError: pass
    else: raise AssertionError('boot/UUID drift')
    cases.append('reject-boot-or-UUID-' + str(len(cases)))
parent = proof('muxretro-provider-session') / 'source/port/scripts/check-phase4-muxretro-provider-session.py'
node = next(n for n in ast.parse(parent.read_text()).body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixture' for t in n.targets))
assert all(isinstance(n,(ast.Expression,ast.Constant,ast.BinOp,ast.Add)) for n in ast.walk(ast.Expression(node.value)))
fixture = eval(compile(ast.Expression(node.value), str(parent), 'eval'), {'__builtins__': {}}, {})
fixture = fixture.split("reset();call('valid-fixed-RAM-launch'")[0]
fixture = fixture.replace('muxretro-provider-session', 'installed-provider-session').replace('c68', 'c73').replace('C68', 'C73')
fixture = fixture.replace('exec "$capsule/host/muxretro"', 'exec /opt/muos/frontend/muxretro')
fixture = fixture.replace("old=Path('/work/muxretro-package/build.mdou4mqr/target')", "old=Path('/work/muxretro-provider/build.f9a1ac69/target')")
fixture = fixture.replace("rows=json.loads(Path('/work/muxretro-install/install.67io22z3/plan.json').read_text())['files']", "rows=[{'path':n,**r} for n,r in json.loads(Path('/work/provider-upgrade-native/install.otw0lflu/plan.json').read_text())['after'].items()]")
fixture = fixture.replace("['lib','provider-lib','host']", "['lib','provider-lib']")
fixture = fixture.replace(" shutil.copyfile(host,cap/'host/muxretro');(cap/'host/muxretro').chmod(0o700)\n", '')
fixture = fixture.replace("str(cap)+'/provider-lib:/opt/muos/frontend/lib'", "'/opt/muos/frontend/lib'")
fixture = fixture.replace("str(cap/'host/muxretro')", "'/opt/muos/frontend/muxretro'")
fixture += '''
reset();call('valid-installed31-launch',True)
reset();call('valid-check-no-execution',True,'check')
reset();(root/'opt/muos/frontend/muxretro').unlink();call('missing-installed-host')
reset();p=root/'opt/muos/frontend/muxretro';p.write_bytes(p.read_bytes()+b'bad');call('corrupt-installed-host')
reset();(root/'opt/muos/frontend/muxretro').chmod(0o700);call('wrong-installed-mode')
reset();p=root/'opt/muos/frontend/muxretro';p.unlink();p.symlink_to(host);call('installed-symlink')
reset();os.link(root/'opt/muos/frontend/muxretro',root/'neighbor');call('installed-hardlink')
reset();(cap/'host').mkdir();call('RAM-host-directory-forbidden')
reset();(cap/'muxretro').write_text('fallback');call('RAM-root-host-forbidden')
reset();(cap/'role').write_text('save\\n');call('writer-role-forbidden')
reset();call('unknown-operation',operation='other')
reset();call('extra-argument',operation='launch ignored')
reset();call('wrong-environment',ld=str(cap)+'/provider-lib:/opt/muos/frontend/lib')
reset();p=root/'opt/muos/frontend/lib/libmuxcom.so';p.write_bytes(p.read_bytes()+b'bad');call('installed-provider-corrupt')
reset();p=root/'usr/share/muos-frontend-libs/payload.sha256';p.write_bytes(p.read_bytes()+b'bad');call('installed-manifest-corrupt')
'''
ast.parse(fixture)
stage = Path(tempfile.mkdtemp(prefix='checks.', dir=AREA))
(stage / 'fixtures.py').write_text(fixture)
cmd = ['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
       '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
       '--tmpfs','/run:rw,nosuid,nodev,size=128m','-v',f'{WORK}:/work:ro,z','-v',f'{REPO}/port:/port:ro,z',
       (WORK/'rootfs-container.iid').read_text().strip(),'python3','/work/'+str((stage/'fixtures.py').relative_to(WORK))]
r = subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('fixtures.'+ext)).write_text(v)
assert r.returncode == 0,(stage,r.stdout[-1200:],r.stderr[-2000:])
shell = [n for n in r.stdout.splitlines() if n.startswith('C73_PASS_')]
assert len(shell)==15
sources = [Path(__file__),REPO/'port/scripts/phase4_installed_provider_session.py',
           REPO/'port/scripts/prepare-phase4-installed-provider-session.py',REPO/'port/scripts/run-phase4-installed-provider-session.py',*NATIVE.glob('*.sh')]
(stage/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C73_INSTALLED31_CHECKS',
    'binding_cases':cases,'dispatcher_cases':shell,'case_count':len(cases)+len(shell),
    'device_accessed':False,'core_or_ROM_executed':False,
    'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in sources}},indent=2)+'\n')
(AREA/'latest-checks').write_text(str(stage)+'\n')
print('C73 installed31 checks passed:',len(cases)+len(shell),stage)
