#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render C61 from the frozen C59 runner, changing only the tested host."""
from pathlib import Path
import ast
repo=Path(__file__).resolve().parents[2]
source=repo/'port/scripts/run-phase4-gb-installed-session.py'
text=source.read_text()
assert text==(repo/'dist/phase4/gameboy-installed-store/source'/source.relative_to(repo)).read_text()
def change(old,new):
 global text
 assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
change('C59 installed CLI GB session with explicit C54/C58 receipts and next-boot binding.',
       'C61 C60 host qualification in RAM; retain C59 historical asset/boot bindings.')
change('from phase4_gb_installed_session import bind_installed_source',
       'from phase4_gb_installed_session import bind_installed_source\nfrom phase4_muxretro_package_session import bind_package_host')
change('args=p.parse_args();',"p.add_argument('--source-session',required=True,type=Path);p.add_argument('--package-build',required=True,type=Path);args=p.parse_args();")
change("session_area=work/'gb-installed-session'", "session_area=work/'muxretro-package-session'")
change("readonly=repo/'port/device/rk-r35s-p0/gb-installed-session'", "readonly=repo/'port/device/rk-r35s-p0/muxretro-package-session'")
change('for n,f in files.items():assert sha(f)==expected[n]', '''# Keep all historical bindings against the old C50 ELF; replace only now.
source_session=args.source_session.resolve();assert source_session.is_relative_to(work/'gb-installed-session')
source_session_report=pinned_report(source_session,'gameboy-installed-store','load/analysis.json')
package_build=args.package_build.resolve();assert package_build.is_relative_to(work/'muxretro-package')
package_proof=repo/'dist/phase4/muxretro-package'
for n,h in sums(package_proof/'SHA256SUMS').items():assert sha(package_proof/n)==h
assert (package_build/'analysis.json').read_bytes()==(package_proof/'analysis.json').read_bytes()
package_report=json.loads((package_build/'analysis.json').read_text())
for n,h in package_report['source_sha256'].items():assert sha(repo/n)==h,n
package_target=package_build/'target'
manifest=package_target/'usr/share/muos-muxretro/payload.sha256'
assert manifest.read_bytes()==(package_proof/'payload.sha256').read_bytes()
for n,h in sums(manifest).items():assert sha(package_target/n.lstrip('/'))==h,n
provenance=json.loads((package_target/'usr/share/muos-muxretro/provenance.json').read_text())
new_host=package_target/'opt/muos/frontend/muxretro';assert not new_host.is_symlink()
for n,h in sums(package_proof/'platform.sha256').items():
 assert n in {'lib/libui.so','lib/libmuxcom.so','lib/libmuxmod.so','lib/libplutosvg.so'}
 common+="printf '%s  %s\\\\n' "+h+' /opt/muos/frontend/'+n+" | sha256sum -c - >/dev/null\\n"
for n,f in files.items():assert sha(f)==expected[n]
files['muxretro']=new_host
expected['muxretro']=bind_package_host(source_session_report,package_report,provenance,args.boot,source_session_report['kernel_boot_id'],identity,assets,sha(new_host))''')
change("assert len(boot_evidence)==3 and re.fullmatch('[0-9a-f-]{36}',boot_evidence[0])", "assert len(boot_evidence)==3 and re.fullmatch('[0-9a-f-]{36}',boot_evidence[0])\nassert boot_evidence[0]==source_session_report['kernel_boot_id'], 'C61 requires the exact observed C59 boot'")
change("remote('prepare',code)", "remote('prepare',code)\nremote('native-ABI',common+f'LD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/lib:/opt/muos/frontend/lib {directory}/muxretro --version\\nLD_BIND_NOW=1 LD_LIBRARY_PATH={directory}/lib:/opt/muos/frontend/lib {directory}/muxretro --help\\n')")
change("'installed-load-returned'", "'package-host-load-returned'")
change("'C59_INSTALLED_CLI_GB_LOAD'", "'C61_PACKAGE_HOST_GB_LOAD'")
change("'host_binary_sha256':br['binary_sha256'],'outcome':outcome", "'host_binary_sha256':expected['muxretro'],'outcome':outcome")
change("(stage/'analysis.json').write_text", """report.update(source_C59_stage=str(source_session),source_C59_analysis_sha256=sha(source_session/'analysis.json'),C60_build_stage=str(package_build),C60_analysis_sha256=sha(package_build/'analysis.json'),C60_proof_sha256=sha(package_proof/'SHA256SUMS'),old_host_binary_sha256=br['binary_sha256'],old_host_checks_historical_only=True,new_ELF_transferred_to_RAM_only=True,native_ABI_passed=True,exact_C59_boot_retained=True,runtime_libmuxmod_override_sha256=lr['binary_sha256'])
report['source_sha256'].update({str(f.relative_to(repo)):sha(f) for f in [repo/'port/scripts/phase4_muxretro_package_session.py',repo/'port/scripts/prepare-phase4-muxretro-package-session.py']})
(stage/'analysis.json').write_text""")
change("print('C59 installed CLI session collected:'", "print('C61 package host session collected:'")
ast.parse(text)
(repo/'port/scripts/run-phase4-muxretro-package-session.py').write_text(text)
# Preserve the prior analyzer and change only experiment/provenance handling.
source=repo/'port/scripts/analyze-phase4-gb-installed-session.py'
text=source.read_text();assert text==(repo/'dist/phase4/gameboy-installed-store/source'/source.relative_to(repo)).read_text()
change('C59 installed CLI session provenance; no shutdown method inferred.','C61 new package host session provenance; C59 same boot is retained.')
change("'C59_INSTALLED_CLI_PERSISTENCE'", "'C61_PACKAGE_HOST_QUALIFICATION'")
change("'C59_INSTALLED_CLI_GB_LOAD'", "'C61_PACKAGE_HOST_GB_LOAD'")
change("(stage/'persistence-analysis.json').write_text", """previous=json.loads((Path(r['source_C59_stage'])/'analysis.json').read_text())
assert previous['kernel_boot_id']==r['kernel_boot_id'] and previous['boot_sequence']==r['boot_sequence']
assert r['host_binary_sha256']!=r['old_host_binary_sha256']
assert r['native_ABI_passed'] and r['new_ELF_transferred_to_RAM_only'] and r['old_host_checks_historical_only']
report.update(new_host_binary_sha256=r['host_binary_sha256'],old_host_tests_reused_for_new_ELF=False,C59_exact_boot_retained=True,new_native_ABI_passed=True,installed_host_modified=False)
(stage/'persistence-analysis.json').write_text""")
ast.parse(text)
(repo/'port/scripts/analyze-phase4-muxretro-package-session.py').write_text(text)
print('C61 runner/analyzer rendered from frozen C59; no device operation')
