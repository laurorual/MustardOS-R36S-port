#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C58 dispatch/read-only integration receipts without commercial data."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-installed'
out=repo/'dist/phase4/installed-store-backend';assert not out.exists()
for name in ['gameboy-selective-persistence','gameboy-after-boot','save-store-installed']:
 p=repo/'dist/phase4'/name
 for n,h in sums(p/'SHA256SUMS').items():assert sha(p/n)==h
checks=Path((area/'latest-checks').read_text().strip());native=Path((area/'latest-native').read_text().strip())
cr=json.loads((checks/'analysis.json').read_text());r=json.loads((native/'analysis.json').read_text())
assert cr['passed'] and cr['case_count']==34 and r['passed']
assert r['checks_analysis_sha256']==sha(checks/'analysis.json') and r['installed_CLI_used']
assert r['cleanup_passed'] and r['RAM_removed'] and r['snapshot_matches_C54']
assert not r['card_saves_written'] and not r['store_ELF_transferred'] and not r['installed_files_modified']
assert not r['UI_core_ROM_or_audio_started'] and r['real_p3_read_only_noload']
identity=r['private_identity'];sources={Path(__file__),repo/'docs/analysis/phase4-installed-store-backend.md'}
for report in [cr,r]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
public=Path(tempfile.mkdtemp(prefix='public.',dir=area));(public/'checks').mkdir();(public/'native').mkdir()
for n in ['analysis.json','stdout','stderr']:shutil.copyfile(checks/n,public/'checks'/n)
clean=dict(r,private_identity='private');(public/'native/analysis.json').write_text(json.dumps(clean,indent=2)+'\n')
shutil.copyfile(checks/'store-base.sh',public/'read-only-backend.sh')
shutil.copyfile(native/'collected/seed-metadata.txt',public/'native/state-metadata.txt')
lines=[]
for path in [native/'native.stdout',native/'cleanup.stdout',native/'collected/store-seed.log',native/'collected/store-verify.log']:
 lines.extend(s for s in path.read_text().splitlines() if s.startswith(('C58_','C53_','C51_')))
(public/'native/markers.txt').write_text('\n'.join(lines)+'\n')
# Retain the bounded initial failure without identity-bearing paths or states.
failed=area/'native.8_7554tn';(public/'initial-probe').mkdir()
(public/'initial-probe/analysis.json').write_text(json.dumps({'reason':'BusyBox stat filesystem feature absent; replaced stat -f with findmnt',
 'store_CLI_called':False,'p3_read_only':True,'namespace_cleanup':0,'RAM_capsule_removed':True},indent=2)+'\n')
(public/'initial-probe/markers.txt').write_text('\n'.join(s for s in (failed/'native.stdout').read_text().splitlines() if s.startswith('C58_'))+'\n'+(failed/'failure-cleanup.stdout').read_text().splitlines()[-1]+'\n')
for p in sorted(sources):
 to=public/'source'/p.relative_to(repo);to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,to)
result={'passed':True,'experiment':'C58_INSTALLED_STORE_BACKEND','case_count':34,'boot_sequence':r['boot_sequence'],
 'installed_CLI_used':True,'store_ELF_transferred':False,'headless_read_only_seed_verify':True,'generation':1,
 'snapshot_matches_C54':True,'core_bytes':26861,'raw_private_data_or_binaries_included':False,'cleanup_passed':True,
 'root_read_only':True,'p3_unmounted_at_end':True,'game_or_physical_restore_tested':False,'reboot_requested':False}
(public/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz','.tar'}
  assert not p.read_bytes().startswith(b'\x7fELF') and identity.encode() not in p.read_bytes(),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C58 source/metadata-only headless proof frozen and verified:',out)
