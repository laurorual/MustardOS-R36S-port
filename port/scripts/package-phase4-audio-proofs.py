#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C26 public evidence; exclude raw audio, private backups and rootfs."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'; area=work/'audio-buffers'; updates=work/'rootfs-candidate'
installed=Path((updates/'latest-update').read_text().strip());plan=json.loads((installed/'plan.json').read_text());assert plan['experiment']=='C26_AUDIO_BUFFERS'
assert json.loads((installed/'install-analysis.json').read_text())['passed']
meta=json.loads((installed/'manifest.json').read_text()); assert sha(installed/'deployment.tar')==meta['deployment_sha256']
tx=Path((updates/'latest-update-checks').read_text().strip());tm=json.loads((tx/'analysis.json').read_text());assert tm['passed'] and tm['plan_sha256']==sha(installed/'plan.json')
qc=Path((area/'latest-quantum-checks').read_text().strip());qm=json.loads((qc/'analysis.json').read_text());assert qm['passed']
pc=Path((work/'runtime-profile/latest-checks').read_text().strip());assert json.loads((pc/'report.json').read_text())['passed']
last=Path((area/'latest').read_text().strip());assert json.loads((last/'analysis.json').read_text())['passed']
assert json.loads((last/'physical-installed.json').read_text())['user_confirmed_clean_audible']
lastmeta=json.loads((last/'session.json').read_text());assert lastmeta['manual_quantum_override'] is None and lastmeta['manual_codec_gain_override'] is None
out=repo/'dist/phase4/audio-buffers-correction';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='proof.',dir=area))
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for name in ['plan.json','manifest.json','install-analysis.json','deployment.tar','survey.stdout','native-inspect.stdout','native-backup.stdout','apply-result.stdout','health-after.stdout','infrastructure-before.stdout','infrastructure-after.stdout']:
 copy(installed/name,public/'installed'/name)
copy(installed/'SHA256SUMS',public/'installed/deployment-SHA256SUMS')
copy(tx/'analysis.json',public/'checks/transaction.json');copy(tx/'stdout',public/'checks/transaction.stdout')
copy(qc/'analysis.json',public/'checks/quantum.json');copy(pc/'report.json',public/'checks/profile.json')
for f in qc.glob('*/fixture.sh'):copy(f,public/'checks'/f.relative_to(qc))
stages=[]
json_names={'session.json','generation.json','analysis.json','start-intent.json','physical-baseline.json','physical-quantum1024.json','physical-monitor.json','physical-codec195.json','physical-installed.json','monitor-intent.json','monitor-routing.json','monitor-analysis.json','monitor-correlation.json'}
labels=['idle','after-navigation','quantum1024-idle','quantum1024-after-navigation','codec195-idle','installed-native','installed-after-navigation']
json_names.update(n+suf for n in labels for suf in ['.json','-graph.json'])
collected_names={'result','report.txt','prepare.log','start.log','stop.log','restore.log','checkpoint.log','preferences-loaded.txt','preferences-saved.txt','brightness-before.txt','brightness-after.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt','volume-before.sha256','volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256','ui-identity.txt','software-volume.txt'}
for s in sorted(area.glob('session.*')):
 if not (s/'analysis.json').exists():continue
 m=json.loads((s/'session.json').read_text())
 if m['boot_sequence']!=lastmeta['boot_sequence']:continue
 assert json.loads((s/'analysis.json').read_text())['passed']; stages.append(s)
 for f in s.iterdir():
  if not f.is_file():continue
  # Explicit public protocol artifacts. Never include monitor.f32 or any
  # directory tree supplied by the device, even if a new one appears later.
  if f.name in json_names or (f.suffix in ['.stdout','.stderr'] and any(v in f.name for v in ['-audio.','-buffers.','-profiler.','codec-gain.','sink-props.','quantum.','health.','first-monitor-install.'])):
   copy(f,public/'sessions'/s.name/f.name)
 for f in (s/'collected').iterdir():
  assert f.is_file() and not f.is_symlink() and f.name in collected_names
  copy(f,public/'sessions'/s.name/'collected'/f.name)
assert len(stages)==5,len(stages)
pins={**plan['source_sha256'],**meta['sources'],**tm['sources'],**qm['source_sha256']}
for name,digest in pins.items():assert sha(repo/name)==digest,name
names=set(pins)|{'port/scripts/phase4-audio-buffers.py','port/scripts/package-phase4-audio-proofs.py','port/device/rk-r35s-p0/audio-buffers/monitor.sh','port/scripts/phase4_candidate.py','port/scripts/run-phase4-candidate-update.py'}
for name in sorted(names):copy(repo/name,public/'source'/name)
report={'passed':True,'boot_sequence':lastmeta['boot_sequence'],'real_sessions':5,'profile_checks':10,'quantum_checks':6,'transaction_checks':14,'user_confirmed_clean_audible_installed_profile':True,'pair':[55,70],'codec_gain':195,'quantum':1024,'no_manual_override_in_final_session':True,'persistent_files_updated':10,'foundation_hashes':96,'new_ELF_or_reboot_or_C12_token':False,'raw_audio_excluded':True,'maximum_volume_or_headphones_or_coldboot_qualified':False}
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(public/'NOTICE.txt').write_text('C26 public controller/profile evidence only. No disk image, GPU blob, raw captured sound, private backup, seed, key or network credential. Original dArkOSen32 preserved. Full acoustic range/headphones/coldboot/full factory image remain unqualified.\n')
(public/'SHA256SUMS').write_text(''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()))
shutil.move(public,out);print('C26 public proof frozen:',out)
