#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C77 boot, fixed-core dispatcher and content checks, no core/ROM execution."""
from pathlib import Path
import ast, copy, json, subprocess, tempfile
from phase4_candidate import sha
from phase4_installed_core_session import *

ctx, prior_stage, prior, provider_stage, provider, online = historical()
report, plan = installed()
AREA.mkdir(exist_ok=True)
for p in NATIVE.glob('*.sh'): subprocess.run(['sh', '-n', str(p)], check=True)
ast.parse(render_online(online))
watch = watch_script('/run/muos-prefs-data.ABC123')
assert CORE in watch and '/host/muxretro ]' not in watch
assert all("grep -Fq '/opt/muos/frontend/lib/" + n in watch for n in NAMES)
subprocess.run(['sh', '-n'], input=watch, text=True, check=True)
uuid = json.loads((C76 / 'manifest.json').read_text())['kernel_boot_id']
boot = report['boot_sequence']
obs = {'passed': True, 'experiment': 'C77_OBSERVED_BOOT', 'boot_sequence': boot,
       'kernel_boot_id': uuid, 'prior_analysis_sha256': sha(prior_stage / 'analysis.json'),
       'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),
       'C66_analysis_sha256': sha(WORK / 'frontend-libs-session/load.o2agwm0q/analysis.json'),
       'C67_analysis_sha256': sha(ctx['C67_stage'] / 'analysis.json'),
       'C72_analysis_sha256': sha(parent.C72 / 'install-analysis.json'),
       'C76_analysis_sha256': sha(C76 / 'install-analysis.json'),
       'root_RO_installed_payload_and_foundation_verified': True, 'infrastructure': 'fixture',
       'agent_requested_reboot': False}
assert bind(prior, provider, obs, boot, uuid) == ctx['C66_report']['libraries']
cases = ['new-boot-binding', 'installed-core-and-provider-map-syntax']
for key, value in [('experiment', 'C73_OBSERVED_BOOT'), ('boot_sequence', True),
                   ('C76_analysis_sha256', '00'*32), ('C72_analysis_sha256', '00'*32),
                   ('C66_analysis_sha256', '00'*32), ('C67_analysis_sha256', '00'*32),
                   ('infrastructure', ''), ('agent_requested_reboot', True),
                   ('root_RO_installed_payload_and_foundation_verified', False)]:
    changed = copy.deepcopy(obs); changed[key] = value
    try: bind(prior, provider, changed, boot, uuid)
    except AssertionError: pass
    else: raise AssertionError(key)
    cases.append('reject-' + key)
for b, u in [(boot-1, uuid), (True, uuid), (boot, '00000000-0000-0000-0000-000000000000')]:
    try: bind(prior, provider, obs, b, u)
    except AssertionError: pass
    else: raise AssertionError('boot/UUID drift')
    cases.append('reject-boot-or-UUID-' + str(len(cases)))

old = (proof('installed-provider-session') / 'checks/fixtures.py').read_text()
fixture = old
fixture = fixture.replace('installed-provider-session', 'installed-core-session').replace('c73', 'c77').replace('C73', 'C77')
fixture = fixture.replace('"$capsule/core.so"', '"/tmp/c77-root' + CORE + '"')
fixture = fixture.replace("str(cap/'core.so')", "str(root/'opt/muos/share/core/gambatte_libretro.so')")
fixture = fixture.replace("source=source.replace('root=/\\n'", "source=source.replace('" + CORE + "','/tmp/c77-root" + CORE + "')\nsource=source.replace('root=/\\n'")
fixture = fixture.replace("for n in ['core.so','private.gb']:", "for n in ['private.gb']:")
fixture = fixture.replace("shutil.copyfile(old/row['path'],p)", "shutil.copyfile((Path('/work/gambatte-package/build.tgnlr06f/target') if row['path'].startswith(('opt/muos/share/core/', 'usr/share/muos-gambatte/', 'usr/share/licenses/muos-gambatte/')) else old)/row['path'],p)")
anchor = "provider=Path('/work/frontend-libs"
fixture = fixture.replace(anchor, "rows+=json.loads(Path('/work/gambatte-install/install.ucdyhb4b/plan.json').read_text())['files']\n" + anchor)
fixture = fixture.replace('valid-installed31-launch','valid-installed40-launch')
fixture += '''
core=root/'opt/muos/share/core/gambatte_libretro.so'
reset();core.unlink();call('missing-core')
reset();core.write_bytes(core.read_bytes()+b'bad');call('corrupt-core')
reset();core.chmod(0o755);call('wrong-core-mode')
reset();core.unlink();core.symlink_to(host);call('core-symlink')
reset();os.link(core,root/'neighbor');call('core-hardlink')
reset();(cap/'core.so').write_text('fallback');call('RAM-core-forbidden')
reset();(cap/'core.so').symlink_to(core);call('RAM-core-alias-forbidden')
reset();(root/'opt/muos/share/core').chmod(0o700);call('core-parent-mode')
reset();p=root/'usr/share/muos-gambatte/payload.sha256';p.write_text('bad');call('core-manifest-corrupt')
reset();p=root/'usr/share/muos-gambatte/license-review.json';p.unlink();call('missing-license-review')

# Test the content manifest and entry before the dispatcher; never execute a core.
import hashlib
app=Path('/port/device/rk-r35s-p0/installed-core-session/app-launch.sh').read_text()
app=app.replace('/mnt/mmc','/tmp/c77-content')
# Absolute core entry is schema-pinned in production. Relocate only this exact
# literal in the disposable fixture, leaving the integrity and arity checks intact.
app=app.replace('/opt/muos/share/core/gambatte_libretro.so',str(core))
Path('/tmp/c77-app.sh').write_text(app)
def app_call(label,ok=False,kind=None):
 reset()
 shutil.rmtree(content.parents[2])
 (cap/'installed-host.sh').write_text(''' + repr('#!/bin/sh\n[ "$2" != launch ] || printf "C77_APP_EXEC\\n"\n') + ''')
 rows=[hashlib.sha256(core.read_bytes()).hexdigest()+'  '+str(core),hashlib.sha256((cap/'private.gb').read_bytes()).hexdigest()+'  private.gb']
 manifest=cap/'gb-assets.sha256';manifest.write_text('\\n'.join(rows)+'\\n');manifest.chmod(0o600)
 if kind=='hash':manifest.write_text('0'*64+'  '+str(core)+'\\n'+rows[1]+'\\n')
 if kind=='schema':manifest.write_text(rows[0].replace(str(core),'core.so')+'\\n'+rows[1]+'\\n')
 if kind=='extra':manifest.write_text(manifest.read_text()+rows[1]+'\\n')
 if kind=='rom':(cap/'private.gb').write_bytes(b'changed')
 if kind=='symlink':manifest.unlink();manifest.symlink_to(cap/'private.gb')
 if kind=='fallback':(cap/'core.so').symlink_to(core)
 if kind=='mode':manifest.chmod(0o644)
 prefix='findmnt() { echo tmpfs; }\\nset -- '+str(cap)+'\\n. /tmp/c77-app.sh\\n'
 r=subprocess.run(['sh','-c',prefix],capture_output=True,text=True,timeout=10)
 assert (r.returncode==0)==ok,(label,r.returncode,r.stdout,r.stderr)
 assert ('C77_APP_EXEC' in r.stdout)==ok,label
 print('C77_PASS_'+label)
app_call('valid-fixed-core-content-manifest',True)
for kind in ['hash','schema','extra','rom','symlink','fallback','mode']:app_call('reject-content-'+kind,kind=kind)
'''
ast.parse(fixture)
assert 'state/core.so' not in '\n'.join((NATIVE / n).read_text() for n in ['select.sh','store-base.sh','installed-store.sh'])
assert STATE in (NATIVE / 'installed-store.sh').read_text()
assert 'case "$op" in seed|verify)' in (NATIVE / 'store-base.sh').read_text()
stage = Path(tempfile.mkdtemp(prefix='checks.', dir=AREA))
(stage / 'fixtures.py').write_text(fixture)
cmd = ['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
       '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
       '--tmpfs','/run:rw,nosuid,nodev,size=128m','-v',f'{WORK}:/work:ro,z','-v',f'{REPO}/port:/port:ro,z',
       (WORK/'rootfs-container.iid').read_text().strip(),'python3','/work/'+str((stage/'fixtures.py').relative_to(WORK))]
r = subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('fixtures.'+ext)).write_text(v)
assert r.returncode == 0,(stage,r.stdout[-1000:],r.stderr[-1800:])
shell = [n for n in r.stdout.splitlines() if n.startswith('C77_PASS_')]
assert len(shell)==33
sources = [Path(__file__),REPO/'port/scripts/phase4_installed_core_session.py',
           REPO/'port/scripts/prepare-phase4-installed-core-session.py',REPO/'port/scripts/run-phase4-installed-core-session.py',*NATIVE.glob('*.sh')]
(stage/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C77_INSTALLED_CORE_CHECKS',
    'binding_cases':cases,'dispatcher_content_cases':shell,'case_count':len(cases)+len(shell),
    'state_namespace_adapter_static_checked':True,'device_accessed':False,'core_or_ROM_executed':False,
    'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in sources}},indent=2)+'\n')
(AREA/'latest-checks').write_text(str(stage)+'\n')
print('C77 checks passed:',len(cases)+len(shell),stage)
