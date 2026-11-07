#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C45 diagnostic cycle receipts without firmware or private preferences."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/launcher-cycle';out=repo/'dist/phase4/launcher-retro-cycle'
assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area));sources={str(Path(__file__).relative_to(repo))}
def copy(src,dst):
 p=public/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
def report(stage,label,current=True,passed=True):
 r=json.loads((stage/'analysis.json').read_text());assert r['passed'] is passed,(stage,r)
 if current:
  for n,h in r['source_sha256'].items():assert sha(repo/n)==h,(stage,n);sources.add(n)
 copy(stage/'analysis.json',label+'/analysis.json');return r
build=Path((area/'latest-build').read_text().strip());br=report(build,'build')
assert sha(build/'frontend-bin/lib/libmuxmod.so')==br['binary_sha256']
checks=Path((area/'latest-checks').read_text().strip());cr=report(checks,'checks')
assert cr['build_stage']==str(build) and cr['binary_sha256']==br['binary_sha256']
for suffix in ['sh','stdout','stderr','exit']:copy(checks/('audit.'+suffix),'checks/audit.'+suffix)
for mode in ['prepare-failure','signal-test','core-failure','cycle','observe']:
 stage=Path((area/('latest-'+mode)).read_text().strip());r=report(stage,mode)
 assert all(r[n] for n in ['cleanup_passed','global_mountinfo_unchanged','root_ro','RAM_removed'])
 assert not r['preferences_persisted']
 recorded=Path(r['host_checks_stage']);assert sha(recorded/'analysis.json')==r['host_checks_sha256']
 assert json.loads((recorded/'analysis.json').read_text())['passed']
 # Prepare/signal never execute the diagnostic library: preserve their earlier
 # approved receipts when only the launcher hook/library changes.
 if mode not in ['prepare-failure','signal-test']:
  assert r['library_sha256']==br['binary_sha256']
  assert r['host_checks_sha256']==sha(checks/'analysis.json')
 for n in ['intent.json','dispatch.json']:copy(stage/n,mode+'/'+n)
 for prefix in ['preflight','prepare','native','postflight','mount-health','cleanup']:
  for suffix in ['sh','stdout','stderr','exit']:copy(stage/(prefix+'.'+suffix),mode+'/'+prefix+'.'+suffix)
 copy(stage/'collected/result.txt',mode+'/result.txt')
 for log in ['core.log','dispatch.log','game.log','return.log']:
  p=stage/'collected'/log
  if not p.exists():continue
  text=p.read_text();lines=[line for line in text.splitlines() if re.search(r'^C4[45]_|^RETRO_RUNNER_|SDL Renderer Method:|Audio device opened at|Exit frame mirrored',line)]
  (public/mode/(log+'.markers')).write_text('\n'.join(re.sub(r'\x1b\[[0-9;]*m','',line) for line in lines)+'\n')
 if mode in ['core-failure','cycle','observe']:
  for phase,action in [('dispatch','port-retro-diagnostic'),('return','port-cycle-done')]:
   text=(stage/'collected'/(phase+'.log')).read_text()
   assert re.search(r'^C45_LAUNCHER_PRESENT phase='+phase+r' serial=[1-9][0-9]*$',text,re.M)
   assert 'C45_LAUNCHER_EXIT action='+action in text
   assert (stage/'collected'/(phase+'-action.txt')).read_text()==action+'\n'
   copy(stage/'collected'/(phase+'-action.txt'),mode+'/'+phase+'-action.txt')
 if mode in ['cycle','observe']:
  assert re.search(r'^C44_NORMAL_EXIT expired=1 frames=[1-9][0-9]*$',(stage/'collected/game.log').read_text(),re.M)
 if mode=='observe':
  observation=json.loads((stage/'physical-observation.json').read_text())
  assert observation['cycle_qualified']
  copy(stage/'physical-observation.json',mode+'/physical-observation.json')
  for n,h in observation.get('source_sha256',{}).items():assert sha(repo/n)==h;sources.add(n)
  for n in ['observation-active.sh','observation-active.stdout','observation-active.stderr','stopped-screen.sh','stopped-screen.stdout','stopped-screen.stderr','stopped-screen.exit']:
   copy(stage/n,mode+'/'+n)
# Keep the physical regression under the earlier library, never relabel it.
old_observe=area/'observe.hesjp4pt'
report(old_observe,'history/render-regression',current=False)
copy(old_observe/'physical-observation.json','history/render-regression/physical-observation.json')
# Refused first native attempt is historical, with its original source identities.
old=area/'prepare-failure.ohpb_nap';r=report(old,'history/refused-path',current=False,passed=False)
assert r['cleanup_passed'] and r['RAM_removed']
copy(old/'collected/result.txt','history/refused-path/result.txt')
for n in sorted(sources):copy(repo/n,'source/'+n)
(public/'NOTICE.txt').write_text('C45 RAM-only automatic diagnostic launcher -> muxretro -> launcher. Fixed action handoff after real presentation and normal frontend exit; private libmuxmod opt-in. Native partial failure, signal, core-failure/return, normal and supervised cycles recorded separately. Core C40 has digital-zero audio, no acoustic game qualification; no ROM/BIOS. Preferences RO+noload + RAM copy; global runtime/tmp/mounts restored, rootRO/foundation97/network preserved. No firmware installation, reboot, boot token or original32 change. No ELF, image, blob, private preference copy/fingerprint, key, backup, seed or credential included.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C45 public diagnostic cycle proof frozen:',out)
