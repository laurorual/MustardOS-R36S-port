#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C66 new-boot and RAM-library rejection cases; no UI/core/ROM execution."""
from pathlib import Path
import ast, copy, json, subprocess, tempfile
from phase4_candidate import sha
from phase4_frontend_libs_session import historical, bind, current_common, render_online, watch_script, AREA, WORK, REPO, NATIVE

context, prior_stage, prior, provider_stage, provider, online = historical()
AREA.mkdir(exist_ok=True)
old = REPO / 'port/device/rk-r35s-p0/installed-host-session'
for p in NATIVE.glob('*.sh'):
    subprocess.run(['sh', '-n', str(p)], check=True)
app_anchor = 'exec /bin/sh "$capsule/installed-host.sh" "$capsule" launch'
assert (NATIVE / 'app-launch.sh').read_text() == (old / 'app-launch.sh').read_text().replace(app_anchor,
    'export LD_BIND_NOW=1 LD_LIBRARY_PATH="$capsule/provider-lib:/opt/muos/frontend/lib"\n' + app_anchor)
guard_anchor = '[ "$operation" = check ] || [ "$(findmnt -rn -M /mnt/mmc -o FSTYPE)" = tmpfs ]'
assert (NATIVE / 'installed-host.sh').read_text() == (old / 'installed-host.sh').read_text().replace(guard_anchor,
    '/bin/sh "$capsule/frontend-libs.sh" "$capsule" "$operation"\n' + guard_anchor)
generated = render_online(online)
ast.parse(generated)
assert "source_session_report['kernel_boot_id']" not in generated
assert "observation['kernel_boot_id']" in generated
assert 'native-provider-ABI' in generated and 'provider-probe' in generated
subprocess.run(['sh', '-n'], input=watch_script('/run/muos-prefs-data.ABC123'), text=True, check=True)
uuid = '00000000-0000-0000-0000-000000000071'
obs = {'passed': True, 'experiment': 'C66_OBSERVED_BOOT', 'boot_sequence': 71, 'kernel_boot_id': uuid,
       'prior_analysis_sha256': sha(prior_stage / 'analysis.json'),
       'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),
       'root_RO_installed_payload_and_foundation_verified': True, 'infrastructure': 'fixture', 'agent_requested_reboot': False}
assert bind(prior, provider, obs, 71, uuid) == {n: v['sha256'] for n, v in provider['libraries'].items()}
cases = ['valid-new-observed-boot', 'historical-C63-guard-and-caller-exact-deltas', 'generated-code-and-watch-syntax']
mutations = [
 ('wrong-boot', lambda p, v, o, a: a.update(boot=72)),
 ('bool-boot', lambda p, v, o, a: a.update(boot=True)),
 ('wrong-UUID', lambda p, v, o, a: a.update(uuid='00000000-0000-0000-0000-000000000072')),
 ('invalid-UUID', lambda p, v, o, a: a.update(uuid='invalid')),
 ('historical-UUID', lambda p, v, o, a: (o.update(kernel_boot_id=p['kernel_boot_id']), a.update(uuid=p['kernel_boot_id']))),
 ('historical-boot', lambda p, v, o, a: (o.update(boot_sequence=70), a.update(boot=70))),
 ('observation-drift', lambda p, v, o, a: o.update(prior_analysis_sha256='00'*32)),
 ('provider-drift', lambda p, v, o, a: o.update(provider_analysis_sha256='00'*32)),
 ('observation-failed', lambda p, v, o, a: o.update(passed=False)),
 ('unverified-root', lambda p, v, o, a: o.update(root_RO_installed_payload_and_foundation_verified=False)),
 ('agent-reboot', lambda p, v, o, a: o.update(agent_requested_reboot=True)),
 ('missing-infra', lambda p, v, o, a: o.update(infrastructure='')),
 ('provider-diagnostic-variant', lambda p, v, o, a: v.update(C46_diagnostic_variant_included=True)),
 ('private-SDK-provider', lambda p, v, o, a: v.update(private_prebuilt_frontend_SDK_used=True)),
 ('unclean-build', lambda p, v, o, a: v.update(clean_source_build=False)),
 ('historical-save-role', lambda p, v, o, a: p.update(mode='save'))]
for key in ['passed', 'root_ro', 'RAM_removed', 'cleanup_passed', 'global_mountinfo_unchanged',
            'store_matches_previous_boot', 'installed_host_used', 'installed_host_guard_passed']:
    mutations.append(('prior-' + key, lambda p, v, o, a, key=key: p.update({key: False})))
for label, mutate in mutations:
    pr, pv, ob = map(copy.deepcopy, [prior, provider, obs])
    a = {'boot': 71, 'uuid': uuid}
    mutate(pr, pv, ob, a)
    try:
        bind(pr, pv, ob, a['boot'], a['uuid'])
    except AssertionError:
        pass
    else:
        raise AssertionError(label)
    cases.append(label)
assert current_common(context['common'], 70, 71).count('= 71 ]') == 3
stage = Path(tempfile.mkdtemp(prefix='checks.', dir=AREA))
fixture = r'''
from pathlib import Path
import os,shutil,subprocess,json
cap=Path('/run/muos-prefs-data.ABC123')
root=Path('/work/frontend-libs/build.84o1r4aj/target/opt/muos/frontend/lib')
names=['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so']
rows=['provider-lib/'+n for n in names]+['lib/'+n for n in names if n!='libmuxmod.so']
guard='/port/device/rk-r35s-p0/frontend-libs-session/frontend-libs.sh'
def reset():
 if cap.exists():shutil.rmtree(cap)
 cap.mkdir(mode=0o700)
 for name in ['lib','provider-lib']:(cap/name).mkdir(mode=0o700)
 for name in rows:
  shutil.copyfile(root/Path(name).name,cap/name);(cap/name).chmod(0o700)
def call(label,valid=False,operation='launch',ld=None,fs='tmpfs',path=None):
 code='findmnt() { echo "$C66_FS"; }'+chr(10)
 code+='set -- '+str(path or cap)+' '+operation+chr(10)
 code+='. '+guard+chr(10)
 env={**os.environ,'C66_FS':fs,'LD_BIND_NOW':'1','LD_LIBRARY_PATH':str(cap)+'/provider-lib:/opt/muos/frontend/lib'}
 if ld is not None:env['LD_LIBRARY_PATH']=ld
 r=subprocess.run(['sh','-c',code],capture_output=True,text=True,env=env,timeout=8)
 assert (r.returncode==0)==valid,(label,r.returncode,r.stderr)
 print('C66_PASS_'+label)
reset();call('valid-launch',True)
reset();call('valid-check',True,'check',ld='')
for name in rows:
 reset();p=cap/name;p.write_bytes(p.read_bytes()+b'bad');call('hash-'+name)
 reset();(cap/name).chmod(0o644);call('mode-'+name)
 reset();(cap/name).unlink();(cap/name).symlink_to(root/Path(name).name);call('symlink-'+name)
 reset();os.link(cap/name,cap/'extra');call('extra-link-'+name)
reset();shutil.rmtree(cap/'provider-lib');call('missing-provider')
reset();(cap/'lib').chmod(0o755);call('wrong-menu-dir-mode')
reset();shutil.move(cap/'provider-lib',cap/'original');(cap/'provider-lib').symlink_to(cap/'original');call('provider-dir-symlink')
reset();call('wrong-LD-path',ld='/opt/muos/frontend/lib')
reset();call('empty-LD-path',ld='')
reset();call('unknown-operation',operation='save')
reset();call('extra-argument',operation='launch ignored')
reset();call('capsule-not-tmpfs',fs='ext4')
reset();call('capsule-wrong-path',path='/tmp/other')
'''
(stage / 'fixtures.py').write_text(fixture)
ast.parse(fixture)
container = (WORK / 'rootfs-container.iid').read_text().strip()
rel = '/work/' + str(stage.relative_to(WORK))
cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all', '--security-opt=no-new-privileges',
       '--userns=keep-id:uid=0,gid=0', '--user=0', '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m',
       '--tmpfs', '/run:rw,nosuid,nodev,size=128m', '-v', f'{WORK}:/work:ro,z',
       '-v', f'{REPO}/port:/port:ro,z', container, 'python3', rel + '/fixtures.py']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
    (stage / ('fixtures.' + suffix)).write_text(value)
assert r.returncode == 0, (stage, r.stdout[-1000:], r.stderr[-1500:])
shell_cases = [s for s in r.stdout.splitlines() if s.startswith('C66_PASS_')]
sources = [Path(__file__), REPO / 'port/scripts/phase4_frontend_libs_session.py',
           REPO / 'port/scripts/prepare-phase4-frontend-libs-session.py',
           REPO / 'port/scripts/run-phase4-frontend-libs-session.py', *NATIVE.glob('*.sh')]
report = {'passed': True, 'experiment': 'C66_PROVIDER_SESSION_CHECKS', 'binding_cases': cases,
          'library_guard_cases': shell_cases, 'case_count': len(cases) + len(shell_cases),
          'historical_C63_checks_reused': 104, 'device_accessed': False, 'ROM_or_core_executed': False,
          'source_sha256': {str(p.relative_to(REPO)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(AREA / 'latest-checks').write_text(str(stage) + '\n')
print('C66 new binding/provider guards passed:', report['case_count'], stage)
