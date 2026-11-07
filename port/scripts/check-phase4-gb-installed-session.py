#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C59 exact next-boot receipt binding and runner delta; no device replay."""
from pathlib import Path
import ast,copy,json,subprocess,tempfile
from phase4_candidate import sha,sums
from phase4_gb_installed_session import bind_installed_source
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-installed-session';area.mkdir(exist_ok=True)
for name in ['gameboy-after-boot','installed-store-backend','save-store-installed']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
renderer=repo/'port/scripts/prepare-phase4-gb-installed-session.py';runner=repo/'port/scripts/run-phase4-gb-installed-session.py'
before=runner.read_bytes();subprocess.run(['python3',str(renderer)],check=True,capture_output=True);assert runner.read_bytes()==before
ast.parse(runner.read_text());text=runner.read_text()
assert "'save-store':" not in text and "assert 'save-store' not in files" in text
assert "common+=package_health" in text and "installed-store.sha256" in text
assert "installed_origin=bind_installed_source" in text
identity='ab'*32;assets={'ROM_sha256':'cd'*32,'core_sha256':'ef'*32,'save_store_binary_sha256':'01'*32}
prior=dict(experiment='C54_PRIOR_BOOT_GB_LOAD',passed=True,cleanup_passed=True,RAM_removed=True,private_identity=identity,boot_sequence=69,
 mode='load',outcome='load-after-boot-returned',root_ro=True,store_matches_previous_boot=True,**assets)
installed=dict(experiment='C58_INSTALLED_STORE_HEADLESS',passed=True,cleanup_passed=True,RAM_removed=True,private_identity=identity,boot_sequence=69,
 root_read_only=True,global_mountinfo_unchanged=True,snapshot_matches_C54=True,real_p3_read_only_noload=True,
 installed_CLI_used=True,store_ELF_transferred=False,card_saves_written=False,installed_files_modified=False,
 source_snapshot_generation=1,core_bytes=26861,source_C54_analysis_sha256='23'*32)
cases=[]
assert bind_installed_source(prior,installed,70,identity,assets,'23'*32)==69;cases.append('C54-C58-next-boot70')
for label,mutate in [
 ('same-boot',lambda p,i,a:a.update(boot=69)),('skipped-boot',lambda p,i,a:a.update(boot=71)),
 ('bool-counter',lambda p,i,a:a.update(boot=True)),('different-source-boots',lambda p,i,a:i.update(boot_sequence=68)),
 ('prior-failed',lambda p,i,a:p.update(passed=False)),('installed-failed',lambda p,i,a:i.update(passed=False)),
 ('cleanup-failed',lambda p,i,a:i.update(cleanup_passed=False)),('RAM-remains',lambda p,i,a:p.update(RAM_removed=False)),
 ('wrong-identity',lambda p,i,a:i.update(private_identity='00'*32)),('prior-writer',lambda p,i,a:p.update(mode='save')),
 ('wrong-prior-outcome',lambda p,i,a:p.update(outcome='failed')),('prior-root-rw',lambda p,i,a:p.update(root_ro=False)),
 ('prior-store-drift',lambda p,i,a:p.update(store_matches_previous_boot=False)),('installed-root-rw',lambda p,i,a:i.update(root_read_only=False)),
 ('mounts-changed',lambda p,i,a:i.update(global_mountinfo_unchanged=False)),('snapshot-drift',lambda p,i,a:i.update(snapshot_matches_C54=False)),
 ('p3-rw',lambda p,i,a:i.update(real_p3_read_only_noload=False)),('RAM-ELF',lambda p,i,a:i.update(store_ELF_transferred=True)),
 ('not-installed',lambda p,i,a:i.update(installed_CLI_used=False)),('card-written',lambda p,i,a:i.update(card_saves_written=True)),
 ('package-modified',lambda p,i,a:i.update(installed_files_modified=True)),('generation-mismatch',lambda p,i,a:i.update(source_snapshot_generation=2)),
 ('metadata-size',lambda p,i,a:i.update(core_bytes=1)),('receipt-mismatch',lambda p,i,a:i.update(source_C54_analysis_sha256='00'*32)),
 ('ROM-mismatch',lambda p,i,a:p.update(ROM_sha256='00'*32)),('core-mismatch',lambda p,i,a:p.update(core_sha256='00'*32)),
 ('CLI-mismatch',lambda p,i,a:p.update(save_store_binary_sha256='00'*32)),('wrong-experiment',lambda p,i,a:i.update(experiment='C53'))]:
 p,i=copy.deepcopy(prior),copy.deepcopy(installed);a={'boot':70};mutate(p,i,a)
 try:bind_installed_source(p,i,a['boot'],identity,assets,'23'*32)
 except AssertionError:pass
 else:raise AssertionError(label)
 cases.append(label)
# Existing C58 dispatch fixtures and C45 lifecycle failure receipts are reused
# for byte-identical scripts; only this new binding/runner delta is exercised.
checks=Path((work/'gb-installed/latest-checks').read_text().strip());r=json.loads((checks/'analysis.json').read_text());assert r['passed'] and r['case_count']==34
for n,h in r['source_sha256'].items():assert sha(repo/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
sources=[Path(__file__),renderer,runner,repo/'port/scripts/phase4_gb_installed_session.py',repo/'port/device/rk-r35s-p0/gb-installed-session/stopped-screen.sh']
report={'passed':True,'experiment':'C59_SESSION_BINDING_CHECKS','case_count':len(cases),'cases':cases,'C58_dispatch_checks_reused':34,
 'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C59 explicit binding/runner delta passed:',len(cases),stage)
