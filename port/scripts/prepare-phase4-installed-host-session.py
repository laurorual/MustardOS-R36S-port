#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render C63 as a pinned C61 delta: guard and execute the installed host."""
from pathlib import Path
import ast
repo=Path(__file__).resolve().parents[2]
source=repo/'port/scripts/run-phase4-muxretro-package-session.py'
text=source.read_text();assert text==(repo/'dist/phase4/muxretro-package-session/source'/source.relative_to(repo)).read_text()
def change(old,new):
 global text
 assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
change('C61 C60 host qualification in RAM; retain C59 historical asset/boot bindings.','C63 installed muxretro and installed store; no host ELF in the RAM capsule.')
change('from phase4_muxretro_package_session import bind_package_host','from phase4_muxretro_package_session import bind_package_host\nfrom phase4_installed_host_session import bind_installed_host')
change('args=p.parse_args();',"p.add_argument('--source-qualified',required=True,type=Path);p.add_argument('--source-deployment',required=True,type=Path);args=p.parse_args();")
change("session_area=work/'muxretro-package-session'","session_area=work/'installed-host-session'")
change("readonly=repo/'port/device/rk-r35s-p0/muxretro-package-session'","readonly=repo/'port/device/rk-r35s-p0/installed-host-session'")
anchor="area=session_area;area.mkdir(exist_ok=True)"
change(anchor,'''qualified_stage=args.source_qualified.resolve();assert qualified_stage.is_relative_to(work/'muxretro-package-session')
qualified_report=pinned_report(qualified_stage,'muxretro-package-session','load/analysis.json')
deployment_stage=args.source_deployment.resolve();assert deployment_stage.is_relative_to(work/'muxretro-install')
host_proof=repo/'dist/phase4/muxretro-installed'
for n,h in sums(host_proof/'SHA256SUMS').items():assert sha(host_proof/n)==h,n
for n in ['plan.json','install-analysis.json']:
 assert (deployment_stage/n).read_bytes()==(host_proof/n).read_bytes()
deployment_report=json.loads((deployment_stage/'install-analysis.json').read_text())
deployment_plan=json.loads((deployment_stage/'plan.json').read_text())
host_digest=bind_installed_host(qualified_report,deployment_report,deployment_plan,args.boot,source_session_report['kernel_boot_id'],identity,{**assets,'host_binary_sha256':expected['muxretro']},sha(deployment_stage/'plan.json'))
assert deployment_plan['C61_proof_sha256']==sha((repo/'dist/phase4/muxretro-package-session')/'SHA256SUMS')
assert deployment_plan['C60_proof_sha256']==sha(package_proof/'SHA256SUMS')
host_health=(host_proof/'final-health.sh').read_text().split('for name in udevd',1)[0]
common+=host_health
del files['muxretro'];del expected['muxretro']
files.update({'app-launch.sh':readonly/'app-launch.sh','installed-host.sh':readonly/'installed-host.sh'})
expected.update({n:sha(files[n]) for n in ['app-launch.sh','installed-host.sh']})
assert 'muxretro' not in files and 'save-store' not in files
'''+anchor)
change("sha(extra/'app-launch.sh')} > {directory}/launcher.sha256", "sha(files['app-launch.sh'])} > {directory}/launcher.sha256")
change("remote('native-ABI',common+f'LD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/lib:/opt/muos/frontend/lib {directory}/muxretro --version\\nLD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/lib:/opt/muos/frontend/lib {directory}/muxretro --help\\n')", "remote('installed-host-check',common+f'/bin/sh {directory}/installed-host.sh {directory} check\\n')")
change("'package-host-load-returned'", "'installed-host-load-returned'")
change("'C61_PACKAGE_HOST_GB_LOAD'", "'C63_INSTALLED_HOST_GB_LOAD'")
change("'host_binary_sha256':expected['muxretro'],'outcome':outcome", "'host_binary_sha256':host_digest,'outcome':outcome")
change("new_ELF_transferred_to_RAM_only=True", "new_ELF_transferred_to_RAM_only=False")
change("(stage/'analysis.json').write_text", """assert game.count('C63_INSTALLED_HOST_VALID files=13 operation=launch')==1
assert (stage/'installed-host-check.stdout').read_text().endswith('C63_INSTALLED_HOST_VALID files=13 operation=check\\n')
assert (out/'store-readonly-before.sha256').read_bytes()==(qualified_stage/'collected/store-readonly-after.sha256').read_bytes()
report.update(installed_host_used=True,host_ELF_transferred=False,installed_host_guard_passed=True,source_C61_stage=str(qualified_stage),source_C61_analysis_sha256=sha(qualified_stage/'analysis.json'),source_C62_stage=str(deployment_stage),C62_plan_sha256=sha(deployment_stage/'plan.json'),C62_proof_sha256=sha(host_proof/'SHA256SUMS'),app_launch_sha256=sha(files['app-launch.sh']),installed_host_guard_sha256=sha(files['installed-host.sh']))
report['source_sha256'].update({str(f.relative_to(repo)):sha(f) for f in [repo/'port/scripts/phase4_installed_host_session.py',repo/'port/scripts/prepare-phase4-installed-host-session.py',readonly/'app-launch.sh',readonly/'installed-host.sh']})
(stage/'analysis.json').write_text""")
change("print('C61 package host session collected:'", "print('C63 installed host session collected:'")
ast.parse(text);(repo/'port/scripts/run-phase4-installed-host-session.py').write_text(text)
source=repo/'port/scripts/analyze-phase4-muxretro-package-session.py'
text=source.read_text();assert text==(repo/'dist/phase4/muxretro-package-session/source'/source.relative_to(repo)).read_text()
change('C61 new package host session provenance; C59 same boot is retained.','C63 installed-host qualification; retain exact historical boot and store receipts.')
change("'C61_PACKAGE_HOST_QUALIFICATION'", "'C63_INSTALLED_HOST_QUALIFICATION'")
change("'C61_PACKAGE_HOST_GB_LOAD'", "'C63_INSTALLED_HOST_GB_LOAD'")
change("r['new_ELF_transferred_to_RAM_only']", "not r['new_ELF_transferred_to_RAM_only']")
change("(stage/'persistence-analysis.json').write_text", """assert r['installed_host_used'] and not r['host_ELF_transferred'] and r['installed_host_guard_passed']
assert game.count('C63_INSTALLED_HOST_VALID files=13 operation=launch')==1
report.update(installed_host_used=True,host_ELF_transferred=False,installed_host_guard_passed=True)
(stage/'persistence-analysis.json').write_text""")
ast.parse(text);(repo/'port/scripts/analyze-phase4-installed-host-session.py').write_text(text)
print('C63 installed host runner/analyzer rendered; no device operation')
