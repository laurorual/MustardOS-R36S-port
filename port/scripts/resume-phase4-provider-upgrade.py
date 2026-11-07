#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Resume C72 read-only verification with the C65 positional probe ABI restored."""
from pathlib import Path
import argparse, ast, json, shutil, sys
from phase4_candidate import sha
from phase4_frontend_libs_session import NAMES

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path)
a = p.parse_args()
stage = a.stage.resolve()
assert stage.is_relative_to(work / 'provider-upgrade-native')
binding = json.loads((stage / 'binding.json').read_text())
source = repo / 'port/scripts/run-phase4-provider-upgrade.py'
assert sha(source) == binding['source_sha256'][str(source.relative_to(repo))]
assert (stage / 'dispatch.exit').read_text() == '0\n'
assert (stage / 'result.stdout').read_text().startswith('0\n')
assert (stage / 'native-tree.exit').read_text() == (stage / 'mounts-after.exit').read_text() == '0\n'
assert not (stage / 'install-analysis.json').exists()
assert (stage / 'native-ABI.exit').read_text() == '3\n'
assert 'undefined symbol: lang' in (stage / 'native-ABI.stderr').read_text()
assert NAMES == ['libui.so', 'libmuxcom.so', 'libmuxmod.so', 'libplutosvg.so']
for suffix in ['sh', 'stdout', 'stderr', 'exit']:
    target = stage / ('native-ABI-positional-failure.' + suffix)
    assert not target.exists()
    shutil.copyfile(stage / ('native-ABI.' + suffix), target)
text = source.read_text()
old = """arguments = ' '.join('/opt/muos/frontend/lib/' + name for name in sorted(
    json.loads((repo / 'dist/phase4/muxretro-provider-session/analysis.json').read_text())['libraries']))"""
new = "arguments = ' '.join('/opt/muos/frontend/lib/' + name for name in " + repr(NAMES) + ')'
assert text.count(old) == 1
text = text.replace(old, new)
ast.parse(text)
# Only the verify branch runs. The frozen deployment source, capsule, before
# backup, binding and completed apply stay unchanged; never allocate/reapply.
sys.argv = [str(source), 'verify', '--host', binding['host'], '--stage', str(stage)]
exec(compile(text, str(source), 'exec'), {'__file__': str(source), '__name__': '__main__'})
r = json.loads((stage / 'install-analysis.json').read_text())
assert r['passed']
r['initial_positional_probe_failure_preserved'] = True
r['C65_probe_positional_ABI_restored'] = NAMES
r['deployment_redispatched'] = False
r['source_sha256'][str(Path(__file__).relative_to(repo))] = sha(Path(__file__))
(stage / 'install-analysis.json').write_text(json.dumps(r, indent=2) + '\n')
print('C72 read-only verification resumed with the pinned C65 positional ABI; apply not repeated')
