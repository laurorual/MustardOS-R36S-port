#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C27 immutable public speaker calibration/install proof; no images/backups."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'volume-calibration';updates=work/'rootfs-candidate'
stage=Path((area/'latest').read_text().strip());assert json.loads((stage/'analysis.json').read_text())['passed']
for level in [0,65]:
 o=json.loads((stage/f'level-{level}-observation.json').read_text());assert o['target_held_at_receipt'] and o['restored55']
meta=json.loads((stage/'manifest.json').read_text());assert meta['codec_target']==meta['restore_codec']==215
native=Path(meta['audio_stage']);assert json.loads((native/'analysis.json').read_text())['passed']
certificate=repo/'port/device/rk-r35s-p0/speaker-calibration.json';cert=json.loads(certificate.read_text());assert cert['codec_gain']==215 and cert['maximum_clean_and_adequate_user_confirmed']
u=Path((updates/'latest-update').read_text().strip());plan=json.loads((u/'plan.json').read_text());assert plan['experiment']=='C27_VOLUME_CALIBRATION' and json.loads((u/'install-analysis.json').read_text())['passed']
tx=Path((updates/'latest-update-checks').read_text().strip());tm=json.loads((tx/'analysis.json').read_text());assert tm['passed'] and tm['plan_sha256']==sha(u/'plan.json')
checks=Path((area/'latest-checks').read_text().strip());cm=json.loads((checks/'analysis.json').read_text());assert cm['passed'] and len(cm['cases'])==13
profile=Path((work/'runtime-profile/latest-checks').read_text().strip());assert json.loads((profile/'report.json').read_text())['passed']
out=repo/'dist/phase4/speaker-volume-calibration';assert not out.exists();public=Path(tempfile.mkdtemp(prefix='proof.',dir=area))
def copy(f,d):d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,d)
for name in ['plan.json','manifest.json','install-analysis.json','deployment.tar','apply-result.stdout','health-after.stdout','native-inspect.stdout','native-backup.stdout','infrastructure-before.stdout','infrastructure-after.stdout']:
 copy(u/name,public/'installed'/name)
copy(u/'SHA256SUMS',public/'installed/deployment-SHA256SUMS')
for label,path,name in [('controller',checks,'analysis.json'),('transaction',tx,'analysis.json'),('profile',profile,'report.json')]:copy(path/name,public/'checks'/(label+'.json'))
copy(checks/'stdout',public/'checks/controller.stdout');copy(checks/'fixtures.py',public/'checks/controller-fixtures.py');copy(tx/'stdout',public/'checks/transaction.stdout')
valid_attempts=[]
for s in sorted(area.glob('calibration.*')):
 if not (s/'analysis.json').exists():continue
 m=json.loads((s/'manifest.json').read_text())
 if m['boot_sequence']!=52:continue
 folder=public/'attempts'/s.name
 for f in s.iterdir():
  if f.is_file() and (f.name in ['manifest.json','analysis.json'] or (f.name.startswith('level-') and f.name.endswith('-observation.json')) or f.name.endswith('-finish.stdout')):copy(f,folder/f.name)
 if (s/'collected').exists():
  for f in (s/'collected').rglob('*'):
   if f.is_file():
    assert not f.is_symlink() and f.stat().st_size<65536
    copy(f,folder/'controller'/f.relative_to(s/'collected'))
 valid_attempts.append(s.name)
 # Bind the selected maximum certificate to the actual observation bytes.
 o=s/'level-100-observation.json'
 if o.exists() and sha(o)==cert['maximum_observation_sha256']:
  assert m['codec_target']==215 and json.loads(o.read_text())['target_held_at_receipt'];maximum_bound=True
assert locals().get('maximum_bound',False)
failure=work/'audio-buffers/session.ki7r_i3z/failed-lease-collection'
assert json.loads((failure/'diagnosis.json').read_text())['session_result']==1
for f in failure.iterdir():
 assert f.is_file() and f.stat().st_size<524288
 copy(f,public/'lease-failure'/f.name)
for f in (native/'collected').iterdir():
 assert f.is_file() and f.stat().st_size<524288
 copy(f,public/'final-native'/f.name)
copy(native/'analysis.json',public/'final-native/analysis.json');copy(certificate,public/'speaker-calibration.json')
pins={**plan['source_sha256'],**tm['sources'],**cm['source_sha256']}
for name,digest in pins.items():assert sha(repo/name)==digest,name
for name in set(pins)|{'port/scripts/phase4-volume-calibration.py','port/scripts/phase4-audio-buffers.py',str(Path(__file__).relative_to(repo))}:
 copy(repo/name,public/'source'/name)
record={'passed':True,'subjective_speaker_UI_calibration':True,'boot_sequence':52,'codec_gain':215,'quantum':1024,'software_zero_silent':True,'software65_clean_comfortable':True,'software100_clean_adequate':True,'saved_pair_unchanged':[55,70],'factory_image_not_written':True,'no_new_token_or_reboot':True,'absolute_SPL_headphones_music_long_duration_qualified':False,'controller_checks':13,'transaction_checks':14,'profile_checks':10,'negative_lease_expiry_preserved':True,'attempts':valid_attempts}
(public/'analysis.json').write_text(json.dumps(record,indent=2)+'\n')
(public/'NOTICE.txt').write_text('C27 subjective speaker/UI calibration and directed profile update. Original32 preserved. No private image/GPU/raw audio/seed/keys/network credentials/private backup or private fingerprint. A lease-expiry result1 is retained as a failed experiment, not relabeled success. Final/native restore and typed55/70 passed.\n')
(public/'SHA256SUMS').write_text(''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()))
shutil.move(public,out);print('Speaker calibration public proof frozen',out)
