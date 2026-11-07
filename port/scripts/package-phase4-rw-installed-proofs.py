#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C33 RW experiment and two-file installation, without private state."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'rootfs-candidate'
stage=Path((area/'latest-update').read_text().strip());plan=json.loads((stage/'plan.json').read_text())
assert plan['experiment']=='C33_ALSA_RW'
assert json.loads((stage/'install-analysis.json').read_text())['passed']
trial=work/'audio-buffers/session.9tikayjz'
assert json.loads((trial/'physical-observation.json').read_text())['sound_clean_and_audible']
assert json.loads((trial/'analysis.json').read_text())['passed']
assert (trial/'rw-final-cleanup.exit').read_text().strip()=='0'
checks=Path((area/'latest-update-checks').read_text().strip());tx=json.loads((checks/'analysis.json').read_text())
assert tx['passed'] and tx['plan_sha256']==sha(stage/'plan.json')
guards=Path((work/'audio-clock-audit/latest-irq-checks').read_text().strip());g=json.loads((guards/'analysis.json').read_text());assert g['passed']
out=repo/'dist/phase4/alsa-rw-installed';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='rw-proof.',dir=work/'audio-clock-audit'))
def copy(source,name):
    assert source.is_file() and not source.is_symlink()
    target=public/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for name in ['plan.json','manifest.json','install-analysis.json','deployment.tar','survey.sh','survey.stdout',
             'apply-result.stdout','health-after.stdout','infrastructure-before.stdout','infrastructure-after.stdout']:
    copy(stage/name,'installation/'+name)
for name in ['session.json','generation.json','irq-configuration.json','irq-wireplumber.conf','trial-foundation.sha256',
             'irq-session.sh','runner-source.py','physical-observation.json','analysis.json']:
    copy(trial/name,'RAM-trial/'+name)
assert sha(trial/'runner-source.py')==json.loads((trial/'session.json').read_text())['source_sha256']
for label in ['rw-audit','physical-receipt','rw-final-cleanup','stop','health']:
    for ext in ['sh','stdout','stderr','exit']:copy(trial/(label+'.'+ext),'RAM-trial/'+label+'.'+ext)
for name in ['result','report.txt','preferences-loaded.txt','preferences-saved.txt','mixer-before.txt','mixer-after.txt',
             'drm-before.txt','drm-after.txt','brightness-before.txt','brightness-after.txt',
             'volume-before.sha256','volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256']:
    copy(trial/'collected'/name,'RAM-trial/collected/'+name)
copy(checks/'analysis.json','checks/transaction.json');copy(checks/'stdout','checks/transaction.stdout')
copy(guards/'analysis.json','checks/wrapper.json');copy(guards/'stdout','checks/wrapper.stdout')
sources=set(plan['source_sha256'])|set(json.loads((stage/'manifest.json').read_text())['sources'])|set(tx['sources'])|set(g['source_sha256'])
sources|={'port/scripts/package-phase4-rw-installed-proofs.py'}
for name in sources:copy(repo/name,'source/'+name)
(public/'analysis.json').write_text(json.dumps({'passed':True,'scope':'C33 installed RW policy; post-reboot qualification separate',
    'boot_sequence_at_install':57,'files_written':2,'foundation_hashes':97,'PCM_access':'RW_INTERLEAVED',
    'gain':215,'quantum':1024,'saved_pair':[55,70],'physical_RAM_audio_clean':True,
    'loudness_low_at_saved55':True,'new_kernel_DTB_ELF_partition_or_image':False,
    'wrapper_checks':len(g['cases']),'transaction_checks':len(tx['cases'])},indent=2)+'\n')
(public/'NOTICE.txt').write_text('C33 public source/configuration and bounded RW experiment/install. Low loudness at saved55 remains a separate observation; gain215 and preference55/70 preserved. No private backup/fingerprint/seed/SSH/network data, raw audio, GPU or rootfs. Full image boot and long-duration audio unqualified.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C33 RW installation proof frozen:',out)
