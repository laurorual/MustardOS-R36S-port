# SPDX-License-Identifier: MIT
"""C66: retain C63 historical bindings, then bind a separately observed boot."""
from pathlib import Path
import ast, json, re, sys
from phase4_candidate import sha, sums

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / 'build/phase4'
AREA = WORK / 'frontend-libs-session'
SOURCE = REPO / 'port/scripts/run-phase4-installed-host-session.py'
NATIVE = REPO / 'port/device/rk-r35s-p0/frontend-libs-session'
NAMES = ['libui.so', 'libmuxcom.so', 'libmuxmod.so', 'libplutosvg.so']

def proof(name):
    root = REPO / 'dist/phase4' / name
    for n, h in sums(root / 'SHA256SUMS').items():
        assert sha(root / n) == h, (name, n)
    return root

def historical():
    """Execute only the frozen offline setup; no historical SSH/runner is called."""
    frozen = proof('installed-host-session')
    text = SOURCE.read_text()
    assert text == (frozen / 'source' / SOURCE.relative_to(REPO)).read_text()
    prior_stage = WORK / 'installed-host-session/load.szcr_1jo'
    prior = json.loads((prior_stage / 'analysis.json').read_text())
    clean = {k: ('private' if k in {'ROM_sha256', 'private_identity', 'kernel_boot_id'} else v)
             for k, v in prior.items()}
    assert clean == json.loads((frozen / 'load/analysis.json').read_text())
    physical = json.loads((prior_stage / 'physical-observation.json').read_text())
    assert physical == json.loads((frozen / 'load/physical-observation.json').read_text())
    for key in ['image_and_navigation_confirmed', 'sound_clean_and_audible_confirmed',
                'restore_to_saved_position_confirmed', 'launcher_return_confirmed']:
        assert physical[key] is True
    anchor = 'area=session_area;area.mkdir(exist_ok=True)\n'
    assert text.count(anchor) == 1
    offline, online = text.split(anchor)
    # Online allocation is excluded by an AST boundary, before any SSH variable/call.
    assert not any(isinstance(n, ast.Name) and n.id == 'ssh' for n in ast.walk(ast.parse(offline)))
    argv = ['C63-offline-history', '--host', '192.168.15.10', '--mode', 'load', '--boot', str(prior['boot_sequence'])]
    for option, key in [('source-save', 'source_save_stage'), ('source-load', 'source_load_stage'),
                        ('source-prior', 'source_C54_stage'), ('source-installed', 'source_C58_stage'),
                        ('source-session', 'source_C59_stage'), ('package-build', 'C60_build_stage'),
                        ('source-qualified', 'source_C61_stage'), ('source-deployment', 'source_C62_stage')]:
        argv += ['--' + option, prior[key]]
    oldargv = sys.argv
    context = {'__file__': str(SOURCE), '__name__': 'c66_offline_history'}
    try:
        sys.argv = argv
        exec(compile(offline, str(SOURCE), 'exec'), context)
    finally:
        sys.argv = oldargv
    provider_proof = proof('frontend-libs')
    provider_stage = WORK / 'frontend-libs/build.84o1r4aj'
    provider = json.loads((provider_stage / 'analysis.json').read_text())
    assert provider == json.loads((provider_proof / 'analysis.json').read_text())
    assert provider['passed'] and provider['four_eager_dlopen_and_C60_version_help_passed']
    assert not provider['C46_diagnostic_variant_included'] and not provider['native_runtime_qualified']
    for n, h in provider['source_sha256'].items():
        assert sha(REPO / n) == h, n
    for n in NAMES:
        assert sha(provider_stage / 'target/opt/muos/frontend/lib' / n) == provider['libraries'][n]['sha256']
    return context, prior_stage, prior, provider_stage, provider, online

def current_common(common, old_boot, new_boot):
    assert type(old_boot) is int and type(new_boot) is int and old_boot < new_boot <= 999999
    old = '= ' + str(old_boot) + ' ]'
    assert common.count(old) == 3
    return common.replace(old, '= ' + str(new_boot) + ' ]')

def bind(prior, provider, observation, boot, boot_id):
    for k in ['passed', 'root_ro', 'RAM_removed', 'cleanup_passed', 'global_mountinfo_unchanged',
              'store_matches_previous_boot', 'installed_host_used', 'installed_host_guard_passed']:
        assert prior[k] is True, k
    assert prior['experiment'] == 'C63_INSTALLED_HOST_GB_LOAD' and prior['mode'] == 'load'
    assert prior['outcome'] == 'installed-host-load-returned'
    assert observation['experiment'] == 'C66_OBSERVED_BOOT' and observation['passed'] is True
    assert type(boot) is int and type(observation['boot_sequence']) is int
    assert prior['boot_sequence'] < boot == observation['boot_sequence'] <= 999999
    assert re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', boot_id)
    assert prior['kernel_boot_id'] != boot_id == observation['kernel_boot_id']
    assert observation['prior_analysis_sha256'] == sha(WORK / 'installed-host-session/load.szcr_1jo/analysis.json')
    assert observation['provider_analysis_sha256'] == sha(WORK / 'frontend-libs/build.84o1r4aj/analysis.json')
    assert provider['passed'] and provider['clean_source_build']
    assert provider['four_eager_dlopen_and_C60_version_help_passed']
    assert not provider['private_prebuilt_frontend_SDK_used'] and not provider['C46_diagnostic_variant_included']
    assert observation['root_RO_installed_payload_and_foundation_verified'] is True
    assert observation['infrastructure'] and observation['agent_requested_reboot'] is False
    return {n: row['sha256'] for n, row in provider['libraries'].items()}

def watch_script(directory):
    assert re.fullmatch('/run/muos-prefs-data[.][a-zA-Z0-9]{6}', directory)
    code = f'''set -eu
first=;game=;returned=
for attempt in $(seq 1 245);do
[ -d {directory} ] || exit 0
for p in $(pidof muxfrontend 2>/dev/null || true);do
 [ "$(readlink /proc/$p/exe 2>/dev/null)" = /opt/muos/frontend/muxfrontend ] || continue
 if grep -Fq '{directory}/lib/libui.so' /proc/$p/maps && grep -Fq '{directory}/lib/libmuxcom.so' /proc/$p/maps && grep -Fq '{directory}/lib/libplutosvg.so' /proc/$p/maps && grep -Fq '{directory}/lib/libmuxmod.so' /proc/$p/maps;then
  if [ -z "$first" ];then first=$p;echo C66_MAP_MENU_FIRST_PROVIDER3_C46
  elif [ -n "$game" ] && [ "$p" != "$first" ] && [ -z "$returned" ];then returned=$p;echo C66_MAP_MENU_RETURN_PROVIDER3_C46;fi
 fi
done
for p in $(pidof muxretro 2>/dev/null || true);do
 [ "$(readlink /proc/$p/exe 2>/dev/null)" = /opt/muos/frontend/muxretro ] || continue
 ok=1
'''
    code += ''.join(f" grep -Fq '{directory}/provider-lib/{n}' /proc/$p/maps || ok=0\n" for n in NAMES)
    return code + f''' if [ "$ok" = 1 ] && [ -z "$game" ];then game=$p;echo C66_MAP_GAME_PROVIDER4_INSTALLED_HOST;fi
done
[ ! -f {directory}/state/done ] || exit 0
[ -z "$returned" ] || exit 0
sleep 1
done
exit 64
'''

def render_online(online):
    def change(old, new):
        nonlocal online
        assert online.count(old) == 1, old
        online = online.replace(old, new)
    end = "log=(out/'core.log').read_text()"
    assert online.count(end) == 1
    online = online.split(end)[0]
    change("assert boot_evidence[0]==source_session_report['kernel_boot_id'], 'C61 requires the exact observed C59 boot'",
           "assert boot_evidence[0]==observation['kernel_boot_id'], 'C66 requires the exact observed new boot'")
    change("before=remote('preflight',common+infra).stdout", "before=remote('preflight',common+infra).stdout\nassert before==observation['infrastructure']")
    change("f'mkdir -m 700 {directory}/lib\\n'", "f'mkdir -m 700 {directory}/lib {directory}/provider-lib\\n'")
    anchor = "remote('installed-host-check',common+f'/bin/sh {directory}/installed-host.sh {directory} check\\n')"
    abi = [
        "provider_args = ' '.join(directory+'/provider-lib/'+n for n in NAMES)",
        "abi_code = f\"\"\"LD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/provider-lib:/opt/muos/frontend/lib {directory}/provider-probe {provider_args}",
        "LD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/provider-lib:/opt/muos/frontend/lib /opt/muos/frontend/muxretro --version",
        "LD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/provider-lib:/opt/muos/frontend/lib /opt/muos/frontend/muxretro --help",
        '\"\"\"',
        "remote('native-provider-ABI',common+abi_code)"]
    change(anchor, anchor + '\n' + '\n'.join(abi) + '\n')
    anchor = "r=remote('native',common+"
    watch = ["watch_code=watch_script(directory)",
             "(stage/'watch-maps.sh').write_text(watch_code)",
             "watch_out=(stage/'watch-maps.stdout').open('w');watch_err=(stage/'watch-maps.stderr').open('w')",
             "watcher=subprocess.Popen(ssh+['sh -s'],stdin=subprocess.PIPE,stdout=watch_out,stderr=watch_err,text=True)",
             "watcher.stdin.write(watch_code);watcher.stdin.close()"]
    change(anchor, '\n'.join(watch) + '\n' + anchor)
    change("health=remote('postflight',common+infra,required=False)", '\n'.join([
        "try: watch_status=watcher.wait(timeout=4)",
        "except subprocess.TimeoutExpired:",
        " watcher.terminate();watch_status=watcher.wait(timeout=4)",
        "watch_out.close();watch_err.close()",
        "(stage/'watch-maps.exit').write_text(str(watch_status)+chr(10))",
        "health=remote('postflight',common+infra,required=False)"]))
    ast.parse(online)
    return online
