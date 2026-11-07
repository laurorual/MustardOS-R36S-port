#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C30 timing improvement and the uninstalled IRQ-policy proposal."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
trial=work/'audio-buffers/session.bvdpctw8'
direct=work/'audio-clock-audit/silent.rshsx1ml'
guards=work/'audio-clock-audit/irq-checks.o7xckims'
candidate=work/'rootfs-candidate/irq-candidate-checks.01goztxg'
analysis=json.loads((trial/'irq-analysis.json').read_text())
assert analysis['technical_passed'] and not analysis['installed_configuration_changed']
assert json.loads((trial/'analysis.json').read_text())['passed']
assert json.loads((direct/'analysis.json').read_text())['passed']
for path,key in [(guards,'source_sha256'),(candidate,'sources')]:
    report=json.loads((path/'analysis.json').read_text());assert report['passed'] and len(report['cases'])==9
    for name,digest in report[key].items(): assert sha(repo/name)==digest,name
destination=repo/'dist/phase4/alsa-irq-ram-preparation';assert not destination.exists()
public=Path(tempfile.mkdtemp(prefix='irq-proof.',dir=work/'audio-clock-audit'))
def copy(path,rel):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<262144,path
    target=public/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
for name in ['session.json','generation.json','analysis.json','irq-analysis.json','physical-observation.json',
             'irq-configuration.json','irq-wireplumber.conf','irq-session.sh','collection-before-stop.json']:
    copy(trial/name,'RAM-trial/'+name)
for label in ['start','irq-prepare','irq-clock-readback','irq-clock-confirmed','irq-final-cleanup','stop','health','collection-before-stop-health']:
    for ext in ['sh','stdout','stderr','exit']:copy(trial/(label+'.'+ext),'RAM-trial/'+label+'.'+ext)
for name in ['result','report.txt','preferences-loaded.txt','preferences-saved.txt','brightness-before.txt',
             'brightness-after.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt',
             'volume-before.sha256','volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256']:
    copy(trial/'collected'/name,'RAM-trial/collected/'+name)
assert sha(direct/'native-probe.sh')==json.loads((direct/'intent.json').read_text())['source_sha256']
for name in ['intent.json','analysis.json','native-probe.sh','probe.sh','probe.stdout','probe.stderr','cleanup.sh','cleanup.stdout','cleanup.exit']:
    copy(direct/name,'same-route-zero/'+name)
for name in ['MMAP_S32_LE-params.txt','MMAP_S32_LE-first.txt','MMAP_S32_LE-second.txt','MMAP_S32_LE-clocks.txt',
             'mixer-before.txt','mixer-active.txt','mixer-after.txt','route-set.log','gain-set.log']:
    copy(direct/'collected'/name,'same-route-zero/collected/'+name)
for label,path in [('wrapper',guards),('candidate',candidate)]:
    copy(path/'analysis.json','checks/'+label+'.json')
    if (path/'stdout').exists():copy(path/'stdout','checks/'+label+'.stdout')
for name in ['opt/muos/device/control/wireplumber.conf','usr/libexec/muos-session/prerequisites.sha256']:
    copy(candidate/'target'/name,'proposal/'+name)
sources=['port/device/rk-r35s-p0/audio-buffers/irq-session.sh',
         'port/device/rk-r35s-p0/audio-buffers/silent-clock-probe.sh',
         'port/scripts/phase4-audio-buffers.py','port/scripts/phase4-silent-clock-audit.py',
         'port/scripts/check-phase4-audio-irq.py','port/scripts/check-phase4-irq-candidate.py',
         'port/scripts/prepare-phase4-irq-update.py','port/scripts/phase4_candidate.py',
         'port/scripts/package-phase4-irq-proofs.py','port/device/rk-r35s-p0/core-wireplumber.conf']
for name in sources:copy(repo/name,'source/'+name)
(public/'analysis.json').write_text(json.dumps({'passed':True,'scope':'technical RAM experiment and proposal preparation',
    'boot_sequence':55,'new_reboot':False,'direct_same_route_rate':json.loads((direct/'analysis.json').read_text())['direct_ALSA_frames_per_second'],
    'IRQ_PCM_rate':analysis['PCM_frames_per_second'],'buffer_warning_lines_at_end':0,
    'auditory_approval':False,'installation_performed':False,'proposed_public_files':2,
    'proposed_foundation_hashes':97,'installed_foundation_hashes':96,'guard_checks':9,'candidate_checks':9,
    'saved_pair':[55,70],'original32_preserved':True},indent=2)+'\n')
(public/'NOTICE.txt').write_text('C30 technical timing improvement only. Physical hearing response was not received in this bounded window; no auditory approval or installation. Two-file proposal includes IRQ configuration and foundation97; live device remains C27/foundation96. No image/blob, raw audio, microphone, seed, SSH/network credential or private backup.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,destination);print('IRQ RAM experiment and proposal frozen:',destination)
