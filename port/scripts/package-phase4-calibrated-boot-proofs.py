#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze bounded launcher evidence, preserving earlier boots during repeats."""
from pathlib import Path
import argparse, json, shutil, tempfile
from phase4_candidate import sha
from phase4_launcher_trial import calibrated_contract
from phase4_repeat_proof import repeat_name

repo = Path(__file__).resolve().parents[2]; area = repo / 'build/phase4/rootfs-candidate'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('operation', choices=['session', 'fallback'])
parser.add_argument('--trial', type=Path, required=True)
parser.add_argument('--repeat-proof', action='store_true', help='Freeze a forward repeat under its actual boot number')
args = parser.parse_args()
trial = args.trial.resolve(); assert trial.is_relative_to(area) and trial.name.startswith('c25-physical.')
meta = json.loads((trial / 'trial.json').read_text())
assert meta['experiment'] in ['C28_CALIBRATED_LAUNCHER_BOOT','C31_IRQ_LAUNCHER_BOOT','C34_RW_LAUNCHER_BOOT','C37_PRIMED_LAUNCHER_BOOT']
prime=meta['experiment']=='C37_PRIMED_LAUNCHER_BOOT'
irq=meta['experiment'] in ['C31_IRQ_LAUNCHER_BOOT','C34_RW_LAUNCHER_BOOT','C37_PRIMED_LAUNCHER_BOOT']
rw=meta['experiment'] in ['C34_RW_LAUNCHER_BOOT','C37_PRIMED_LAUNCHER_BOOT']
installation = Path(meta['installation_stage']); plan = json.loads((installation / 'plan.json').read_text())
contract = calibrated_contract(repo, area, installation, plan)
assert meta['calibrated_contract'] == contract
checks = Path((area / ('latest-irq-launcher-checks' if irq else 'latest-launcher-trial-checks')).read_text().strip())
report = json.loads((checks / 'analysis.json').read_text()); assert report['passed']
for name, digest in report['source_sha256'].items(): assert sha(repo / name) == digest, name
label = 'c25-collect' if args.operation == 'session' else 'c25-fallback'
result = json.loads((trial / (label + '.json')).read_text()); assert result['passed']
assert result['boot_sequence'] == meta['expected_boot' if args.operation == 'session' else 'expected_fallback']
observed = json.loads((trial / 'physical-observation.json').read_text())
assert observed['boot_sequence'] == meta['expected_boot']
assert isinstance(observed['image_and_navigation_normal'], bool) and isinstance(observed['sound_clean_and_audible'], bool)
prefix='primed-launcher' if prime else ('rw-launcher' if rw else ('irq-launcher' if irq else 'calibrated-launcher'))
name = (prefix+'-boot' if observed['sound_clean_and_audible'] else prefix+'-boot-audio-regression') if args.operation == 'session' else prefix+'-fallback'
reference = None
repeat_checks = None
repeat_references = {}
if args.repeat_proof:
    assert prime and observed['sound_clean_and_audible'], 'Negative or non-prime repeats require separate diagnostic evidence'
    from phase4_candidate import sums
    references=[]
    for original in ['primed-launcher-boot','primed-launcher-fallback']:
        folder=repo/'dist/phase4'/original
        for rel,digest in sums(folder/'SHA256SUMS').items():
            assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
            assert sha(folder/rel)==digest
        assert sha(folder/'installation/plan.json')==sha(installation/'plan.json'), 'Repeat must test the same installed plan'
        references.append(json.loads((folder/'analysis.json').read_text()))
        repeat_references[original]={'analysis_sha256':sha(folder/'analysis.json'),'SHA256SUMS_sha256':sha(folder/'SHA256SUMS')}
    reference,previous_fallback=references
    name=repeat_name(prefix,args.operation,meta,reference,previous_fallback)
    repeat_checks=Path((area/'latest-repeat-proof-checks').read_text().strip())
    assert repeat_checks.resolve().is_relative_to(area)
    checked=json.loads((repeat_checks/'analysis.json').read_text()); assert checked['passed']
    for path,digest in checked['source_sha256'].items(): assert sha(repo/path)==digest
destination = repo / 'dist/phase4' / name; assert not destination.exists(), 'Never overwrite frozen evidence'
public = Path(tempfile.mkdtemp(prefix='calibrated-boot-proof.', dir=area))
def copy(source, rel):
    assert source.is_file() and not source.is_symlink()
    target = public / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
if repeat_checks:
    copy(repeat_checks/'analysis.json','repeat-proof-checks.json')
    (public/'repeat-reference.json').write_text(json.dumps(repeat_references,indent=2)+'\n')
for name in ['plan.json', 'manifest.json', 'install-analysis.json']:
    copy(installation / name, 'installation/' + name)
for name in ['trial.json', label + '.json',
             label + '-health.sh', label + '-health.stdout',
             label + '-final-health.sh', label + '-final-health.stdout']:
    copy(trial / name, name)
if (trial/'preparation-retry.json').exists():copy(trial/'preparation-retry.json','preparation-retry.json')
shutil.copytree(trial / label, public / 'collected')
if args.operation == 'session':
    assert json.loads((trial / 'c28-audio-running.json').read_text())['passed']
    for name in ['c25-arm.json', 'c25-reboot.json', 'c25-running.sh', 'c25-running.stdout',
                 'c25-running.json', 'c28-audio-running.json', 'physical-observation.json',
                 'c25-infrastructure-running.stdout', 'c25-infrastructure-stopped.stdout',
                 'post-navigation-audio.sh', 'post-navigation-audio.stdout', 'post-navigation-audio.exit']:
        copy(trial / name, name)
    assert (trial / 'post-navigation-audio.exit').read_text().strip() == '0'
    if prime:
        for label in ['boot-pcm-rate', 'post-navigation-audio']:
            measured=json.loads((trial/(label+'.json')).read_text())
            assert measured['within_two_percent'] and measured['same_owner_and_trigger']
            assert measured['boot_sequence']==meta['expected_boot']
            for ext in ['sh','stdout','exit','json']: copy(trial/(label+'.'+ext),label+'.'+ext)
    if (trial/'preparation-retry.json').exists():
        previous = Path(json.loads((trial / 'preparation-retry.json').read_text())['previous_stage'])
        assert previous.is_relative_to(area)
        for name in ['c25-arm.json', 'c25-arm.sh', 'c25-arm.stdout', 'c25-arm.stderr', 'c25-arm.exit', 'preparation-failure-analysis.json']:
            copy(previous / name, 'preparation-refused/' + name)
    if not observed['sound_clean_and_audible']:
        regression = json.loads((trial / 'audio-regression-analysis.json').read_text())
        assert not regression['audio_qualified'] and regression['physical_distortion_confirmed']
        regression_files=['audio-regression-analysis.json'] if irq else ['audio-regression-analysis.json', 'post-navigation-graph.json',
                     'post-navigation-profiler.sh', 'post-navigation-profiler.stdout',
                     'post-navigation-profiler.stderr', 'post-navigation-profiler.exit',
                     'pcm-clock-readback.sh', 'pcm-clock-readback.stdout', 'pcm-clock-readback.exit']
        for name in regression_files:
            copy(trial / name, name)
else:
    copy(trial / 'c25-fallback-reboot.json', 'c25-fallback-reboot.json')
copy(checks / 'analysis.json', 'host-checks.json')
pins = set(report['source_sha256']) | set(plan['source_sha256'])
pins |= {'port/scripts/package-phase4-calibrated-boot-proofs.py', 'port/scripts/phase4_candidate.py'}
pins.add('port/scripts/phase4_repeat_proof.py')
if repeat_checks: pins.update(checked['source_sha256'])
for name in sorted(pins):
    assert name.startswith('port/') and '..' not in Path(name).parts
    copy(repo / name, 'source/' + name)
(public / 'analysis.json').write_text(json.dumps({
    'passed': observed['sound_clean_and_audible'] if args.operation == 'session' else True,
    'boot_lifecycle_passed': True, 'audio_passed': observed['sound_clean_and_audible'],
    'experiment': meta['experiment'],
    'boot_sequence': result['boot_sequence'], 'selected': result['selected'],
    'profile_codec_gain': 215, 'profile_quantum': 1024, 'saved_pair': [55, 70],
    'calibrated_profile_matches_composition': not irq,
    'installed_candidate_bound': True, 'IRQ_scheduling': irq, 'RW_access': rw,
    'direct_zero_PCM_priming': prime,
    'foundation_hashes': result['foundation_hashes'],
    'new_native_code_or_ELF_installed': False, 'full_factory_image_boot_tested': False,
    'C12_rearmed': False, 'permanent_launcher_enabled': False,
    'physical_observation_in_this_boot': args.operation == 'session',
    'repeat_of_boot': reference['boot_sequence'] if reference else None,
    'host_checks': len(report['cases']), 'durable_reports_match_RAM': True,
    'root_ro_after': True, 'original32_preserved': True}, indent=2) + '\n')
(public / 'NOTICE.txt').write_text(meta['experiment']+' bounded launcher boot/fallback evidence. No rootfs, blobs, raw audio, backup, private fingerprint, seed, SSH key or network credential. Original dArkOSen32 preserved. Complete factory-image boot, cold boot, Power/shutdown/suspend and long-duration operation remain unqualified.\n')
(public / 'SHA256SUMS').write_text(''.join(sha(f) + '  ' + str(f.relative_to(public)) + '\n' for f in sorted(public.rglob('*')) if f.is_file()))
shutil.move(public, destination)
print('Calibrated boot proof frozen:', destination)
