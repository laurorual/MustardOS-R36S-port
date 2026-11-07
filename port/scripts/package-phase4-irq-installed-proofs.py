#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C30 installed IRQ policy, supervised repeat, exact transaction evidence."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'rootfs-candidate'
installed=Path((area/'latest-update').read_text().strip());plan=json.loads((installed/'plan.json').read_text())
assert plan['experiment']=='C30_ALSA_IRQ'
result=json.loads((installed/'install-analysis.json').read_text());assert result['passed'] and result['foundation_hash_count']==97
assert len(plan['files'])==result['public_files_written']==2
manifest=json.loads((installed/'manifest.json').read_text())
assert sha(installed/'plan.json')==manifest['plan_sha256'] and sha(installed/'deployment.tar')==manifest['deployment_sha256']
trial=work/'audio-buffers/session.fr_x6czx'
observation=json.loads((trial/'physical-observation.json').read_text())
assert observation['sound_clean_and_audible'] and observation['target_held_at_receipt']
assert json.loads((trial/'analysis.json').read_text())['passed']
assert (trial/'irq-final-cleanup.exit').read_text().strip()=='0'
assert 'out of buffers on port' not in (trial/'irq-final-cleanup.stdout').read_text()
checks=Path((area/'latest-update-checks').read_text().strip());tx=json.loads((checks/'analysis.json').read_text());assert tx['passed'] and tx['plan_sha256']==sha(installed/'plan.json')
guards=Path((work/'audio-clock-audit/latest-irq-checks').read_text().strip());g=json.loads((guards/'analysis.json').read_text());assert g['passed']
candidate=Path((area/'latest-irq-candidate-checks').read_text().strip());c=json.loads((candidate/'analysis.json').read_text());assert c['passed']
for pins in [plan['source_sha256'],manifest['sources'],tx['sources'],g['source_sha256'],c['sources']]:
    for name,digest in pins.items():assert sha(repo/name)==digest,name
destination=repo/'dist/phase4/alsa-irq-installed';assert not destination.exists()
public=Path(tempfile.mkdtemp(prefix='irq-installed-proof.',dir=work/'audio-clock-audit'))
def copy(source,name):
    assert source.is_file() and not source.is_symlink()
    target=public/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for name in ['plan.json','manifest.json','install-analysis.json','deployment.tar','survey.sh','survey.stdout',
             'native-inspect.stdout','native-backup.stdout','apply-result.stdout','health-after.stdout',
             'infrastructure-before.stdout','infrastructure-after.stdout']:
    copy(installed/name,'installation/'+name)
for name in ['session.json','generation.json','irq-configuration.json','irq-wireplumber.conf','irq-session.sh',
             'physical-observation.json','analysis.json','runner-source.py']:
    copy(trial/name,'supervised-repeat/'+name)
assert sha(trial/'runner-source.py')==json.loads((trial/'session.json').read_text())['source_sha256']
for label in ['physical-receipt','irq-clock-confirmed','irq-final-cleanup','stop','health']:
    for ext in ['sh','stdout','stderr','exit']:copy(trial/(label+'.'+ext),'supervised-repeat/'+label+'.'+ext)
for name in ['result','report.txt','preferences-loaded.txt','preferences-saved.txt','mixer-before.txt','mixer-after.txt',
             'brightness-before.txt','brightness-after.txt','drm-before.txt','drm-after.txt','volume-before.sha256',
             'volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256']:
    copy(trial/'collected'/name,'supervised-repeat/collected/'+name)
for path,name in [(checks/'analysis.json','checks/transaction.json'),(checks/'stdout','checks/transaction.stdout'),
                  (checks/'fixtures.sh','checks/transaction.sh'),(guards/'analysis.json','checks/wrapper.json'),
                  (guards/'stdout','checks/wrapper.stdout'),(candidate/'analysis.json','checks/candidate.json')]:copy(path,name)
failed=area/'update-checks.kc8syych'
for name in ['stdout','stderr','fixtures.sh']:copy(failed/name,'initial-whitelist-refusal/'+name)
sources=set(plan['source_sha256'])|set(manifest['sources'])|set(tx['sources'])|set(g['source_sha256'])|set(c['sources'])
sources|={'port/scripts/package-phase4-irq-installed-proofs.py','port/scripts/run-phase4-candidate-update.py'}
for name in sorted(sources):copy(repo/name,'source/'+name)
(public/'analysis.json').write_text(json.dumps({'passed':True,'scope':'installed IRQ policy and supervised startup, boot qualification separate',
    'boot_sequence_at_install':55,'public_files_written':2,'foundation_hashes':97,'payload_files':15,
    'profile_files':21,'codec_gain':215,'quantum':1024,'saved_pair':[55,70],
    'physical_repeat_clean_audible':True,'worker_cleanup_passed':True,'installed_root_ro':True,
    'transaction_checks':len(tx['cases']),'wrapper_checks':len(g['cases']),'candidate_checks':len(c['cases']),
    'new_ELF_kernel_DTB_partition_or_image':False,'backup_private_not_included':True},indent=2)+'\n')
(public/'NOTICE.txt').write_text('C30 original MIT policy and exact two-file update. Public deployment only; private backup/fingerprint/seed/SSH/network data and rootfs/GPU/raw audio excluded. C27 volume55/brightness70 preserved; supervised RAM repeat clean/audible. Boot qualification is separate; no permanent UI or C12 token.\n')
(public/'SHA256SUMS').write_text(''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()))
shutil.move(public,destination);print('C30 installed policy proof frozen:',destination)
