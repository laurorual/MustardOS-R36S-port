#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render C59's small, audited adaptation of the frozen C54 session runner."""
from pathlib import Path
import ast
repo=Path(__file__).resolve().parents[2]
source=repo/'port/scripts/run-phase4-gb-reboot.py'
text=source.read_text()
assert text==(repo/'dist/phase4/gameboy-after-boot/source'/source.relative_to(repo)).read_text()
def change(old,new):
 global text
 assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
change('C54 prior-boot GB snapshot load; preserve the C53 same-boot runner unchanged.','C59 installed CLI GB session with explicit C54/C58 receipts and next-boot binding.')
change('from phase4_gb_reboot import bind_source','from phase4_gb_reboot import bind_source\nfrom phase4_gb_installed_session import bind_installed_source')
change('args=p.parse_args();',"p.add_argument('--source-prior',required=True,type=Path);p.add_argument('--source-installed',required=True,type=Path);args=p.parse_args();")
anchor="origin=bind_source(source_reports['save'],source_reports['load'],args.boot,identity,assets)"
replacement='''prior_stage=args.source_prior.resolve();assert prior_stage.is_relative_to(work/'gb-reboot')
installed_stage=args.source_installed.resolve();assert installed_stage.is_relative_to(work/'gb-installed')
def pinned_report(stage,proof_name,relative):
 proof=repo/'dist/phase4'/proof_name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 r=json.loads((stage/'analysis.json').read_text())
 clean={k:('private' if k in {'private_identity','ROM_sha256','kernel_boot_id'} else v) for k,v in r.items()}
 assert clean==json.loads((proof/relative).read_text())
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h,n
 return r
prior_report=pinned_report(prior_stage,'gameboy-after-boot','load/analysis.json')
installed_report=pinned_report(installed_stage,'installed-store-backend','native/analysis.json')
origin=bind_source(source_reports['save'],source_reports['load'],prior_report['boot_sequence'],identity,assets)
installed_origin=bind_installed_source(prior_report,installed_report,args.boot,identity,assets,sha(prior_stage/'analysis.json'))
installed_checks=Path((work/'gb-installed/latest-checks').read_text().strip())
ic=json.loads((installed_checks/'analysis.json').read_text());assert ic['passed']
assert sha(installed_checks/'analysis.json')==installed_report['checks_analysis_sha256']
for n,h in ic['source_sha256'].items():assert sha(repo/n)==h
session_area=work/'gb-installed-session'
sc=Path((session_area/'latest-checks').read_text().strip());sr=json.loads((sc/'analysis.json').read_text());assert sr['passed']
for n,h in sr['source_sha256'].items():assert sha(repo/n)==h
package_proof=repo/'dist/phase4/save-store-installed'
for n,h in sums(package_proof/'SHA256SUMS').items():assert sha(package_proof/n)==h
assert sha(package_proof/'SHA256SUMS')==installed_report['C57_proof_sha256']
package_health=(package_proof/'final-health.sh').read_text().split('for name in udevd',1)[0]
assert package_health.count('= 69 ]')==1
common+=package_health.replace('= 69 ]','= '+str(args.boot)+' ]')'''
change(anchor,replacement)
change("readonly=repo/'port/device/rk-r35s-p0/gb-reboot'","readonly=repo/'port/device/rk-r35s-p0/gb-installed-session'")
change("files.update({'save-store':store_checks/'muos-save-store','store.sh':readonly/'store.sh','store-base.sh':extra/'store.sh'})", "installed_sources=repo/'port/device/rk-r35s-p0/gb-installed'\nfiles.update({'store.sh':installed_sources/'store.sh','store-base.sh':installed_checks/'store-base.sh','installed-store.sh':installed_sources/'installed-store.sh'})")
change("expected.update({'save-store':strr['binary_sha256'],'store.sh':sha(readonly/'store.sh'),'store-base.sh':sha(extra/'store.sh')})", "expected.update({n:sha(files[n]) for n in ['store.sh','store-base.sh','installed-store.sh']})\nassert 'save-store' not in files")
change("area=work/'gb-reboot'","area=session_area;area.mkdir(exist_ok=True)")
change("{sha(extra/'store.sh')} > {directory}/store-base.sha256", "{sha(files['store-base.sh'])} > {directory}/store-base.sha256")
change("remote('prepare',code)","code+=f\"printf '%s\\\\n' {sha(files['installed-store.sh'])} > {directory}/installed-store.sha256\\n\"\nremote('prepare',code)")
change("'load-after-boot-returned'","'installed-load-returned'")
change("previous_inventory=(source_stages['load']/'collected/store-readonly-after.sha256').read_bytes()", "previous_inventory=(installed_stage/'collected/store-readonly-after.sha256').read_bytes()\nassert previous_inventory==(prior_stage/'collected/store-readonly-after.sha256').read_bytes()\ninstalled_logs=(out/'store-seed.log').read_text()+(out/'store-verify.log').read_text()\npassed=passed and installed_logs.count('C58_INSTALLED_DISPATCH operation=status')==2 and installed_logs.count('C58_INSTALLED_DISPATCH operation=export')==1")
change("'C54_PRIOR_BOOT_GB_LOAD'","'C59_INSTALLED_CLI_GB_LOAD'")
change("'source_boot_sequence':origin", "'source_boot_sequence':installed_origin,'original_save_boot_sequence':origin")
# Keep the full C54 checks, plus independent installed-package/C58 receipt fields.
change("(stage/'analysis.json').write_text", "report.update(installed_CLI_used=True,store_ELF_transferred=False,source_C54_analysis_sha256=sha(prior_stage/'analysis.json'),source_C58_analysis_sha256=sha(installed_stage/'analysis.json'),source_C58_stage=str(installed_stage),source_C54_stage=str(prior_stage),session_checks_analysis_sha256=sha(sc/'analysis.json'))\nreport['source_sha256'].update({str(f.relative_to(repo)):sha(f) for f in [repo/'port/scripts/phase4_gb_installed_session.py',repo/'port/scripts/prepare-phase4-gb-installed-session.py',installed_sources/'store.sh',installed_sources/'installed-store.sh']})\n(stage/'analysis.json').write_text")
# The old readonly path was used only by source recording and stopped-screen.
change("readonly/'store.sh',screen", "installed_sources/'store.sh',screen")
change("print('C54 prior-boot snapshot session collected:'", "print('C59 installed CLI session collected:'")
ast.parse(text)
output=repo/'port/scripts/run-phase4-gb-installed-session.py';output.write_text(text)
print('C59 runner rendered from pinned C54; no device operation:',output)
