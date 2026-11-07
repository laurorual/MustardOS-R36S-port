#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C46 native guards, physical cancel and selection/return without private data."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/app-selection';out=repo/'dist/phase4/native-app-selection'
assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area));sources={str(Path(__file__).relative_to(repo))}
def copy(src,dst):
 p=public/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
def report(stage,label,current=True):
 r=json.loads((stage/'analysis.json').read_text());assert r['passed'],(stage,r)
 if current:
  for n,h in r['source_sha256'].items():assert sha(repo/n)==h,(stage,n);sources.add(n)
 copy(stage/'analysis.json',label+'/analysis.json');return r
build=Path((area/'latest-build').read_text().strip());br=report(build,'build')
assert sha(build/'frontend-bin/lib/libmuxmod.so')==br['binary_sha256']
checks=Path((area/'latest-checks').read_text().strip());cr=report(checks,'checks')
assert cr['build_stage']==str(build) and cr['binary_sha256']==br['binary_sha256']
for ext in ['sh','stdout','stderr','exit']:copy(checks/('audit.'+ext),'checks/audit.'+ext)
assert cr['real_upstream_writer_bytes_verified']
for n,h in cr['upstream_source_sha256'].items():assert sha(Path(n))==h
for n in ['real-action','real-application']:copy(checks/n,'checks/'+n+'.txt')
for label,pointer,outcome in [('guards','latest-cycle','native-guards-only'),('cancel','latest-cancel','cancelled'),('selection','latest-selection','selected-app-returned')]:
 stage=Path((area/pointer).read_text().strip());r=report(stage,label,current=label!='cancel')
 assert r['outcome']==outcome
 if label!='cancel':assert r['library_sha256']==br['binary_sha256']
 recorded=Path(r['host_checks_stage']);assert sha(recorded/'analysis.json')==r['host_checks_sha256']
 if label=='cancel':
  # B's branch and frontend source are unchanged; only its deadline grew.
  previous_build=Path(json.loads((recorded/'analysis.json').read_text())['build_stage'])
  old_header=(previous_build/'frontend-source/module/port_app_selection.h').read_text()
  assert old_header.replace('60000U','120000U')==(repo/'port/diagnostics/phase4-app-selection.h').read_text()
  assert sha(previous_build/'frontend-source/module/muxapp.c')==sha(build/'frontend-source/module/muxapp.c')
  fixture=recorded/'cancel/select.sh'
  old=fixture.read_text().replace(str(fixture.parent/'runtime'),'/run/muos')
  new=(repo/'port/device/rk-r35s-p0/app-selection/select.sh').read_text()
  def cancellation(text):
   start=text.index('for kind in cancel timeout;do');end=text.index('\ndone\n',start)+6;return text[start:end]
  assert cancellation(old)==cancellation(new)
  (public/label/'unchanged-cancellation-branch.sh').write_text(cancellation(new)+'\n')
  assert r['worker_sha256']==sha(repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh')
 else:assert r['host_checks_sha256']==sha(checks/'analysis.json')
 assert all(r[n] for n in ['cleanup_passed','root_ro','RAM_removed','global_mountinfo_unchanged']) and not r['preferences_persisted']
 for n in ['intent.json','dispatch.json']:copy(stage/n,label+'/'+n)
 for prefix in ['preflight','prepare','native','postflight','mount-health','cleanup','stopped-screen']:
  for ext in ['sh','stdout','stderr','exit']:copy(stage/(prefix+'.'+ext),label+'/'+prefix+'.'+ext)
 copy(stage/'collected/result.txt',label+'/result.txt')
 for log in ['core.log','dispatch.log','game.log','return.log']:
  p=stage/'collected'/log
  if p.exists():
   lines=[s for s in p.read_text().splitlines() if re.search(r'^C4[456]_|^RETRO_RUNNER_',s)]
   (public/label/(log+'.markers')).write_text('\n'.join(lines)+'\n')
 if label!='guards':
  obs=json.loads((stage/'physical-observation.json').read_text());assert obs['qualified']
  copy(stage/'physical-observation.json',label+'/physical-observation.json')
  for n in ['observation-active.sh','observation-active.stdout']:
   if (stage/n).exists():copy(stage/n,label+'/'+n)
 if label=='selection':
  assert (stage/'collected/selected-action.txt').read_text()=='app\n'
  assert (stage/'collected/selected-application.txt').read_text()=='/opt/muos/config/port-apps/R35S-Diagnostic'
  for n in ['selected-action.txt','selected-application.txt','application-governor.txt','application-controller.txt']:copy(stage/'collected'/n,label+'/'+n)
old=area/'cycle.85guoo0j';negative=json.loads((old/'analysis.json').read_text());assert not negative['passed'] and negative['cleanup_passed'] and negative['RAM_removed']
copy(old/'analysis.json','history/missing-bundled-directory/analysis.json');copy(old/'collected/result.txt','history/missing-bundled-directory/result.txt')
failed=area/'observe.fn6v2kt7'
r=json.loads((failed/'analysis.json').read_text());assert not r['passed'] and r['cleanup_passed'] and r['RAM_removed']
for n in ['analysis.json','physical-observation.json']:copy(failed/n,'history/native-CHAR-payload/'+n)
copy(failed/'collected/core.log','history/native-CHAR-payload/core-markers.txt')
failed_return=area/'observe.ox7plzw_'
r=json.loads((failed_return/'analysis.json').read_text());assert not r['passed'] and r['cleanup_passed'] and r['RAM_removed']
for n in ['analysis.json','physical-observation.json']:copy(failed_return/n,'history/stale-governor/'+n)
missed=area/'observe.tjq6258h';r=json.loads((missed/'analysis.json').read_text());assert r['passed'] and r['outcome']=='timed-out' and r['cleanup_passed']
for n in ['analysis.json','physical-observation.json']:copy(missed/n,'history/missed-window/'+n)
missed_again=area/'observe.w84de_5z';r=json.loads((missed_again/'analysis.json').read_text());assert r['outcome']=='timed-out' and r['cleanup_passed']
for n in ['analysis.json','physical-observation.json']:copy(missed_again/n,'history/second-missed-window/'+n)
for n in sorted(sources):copy(repo/n,'source/'+n)
(public/'NOTICE.txt').write_text('C46 native muxapp A selection, B cancel, one fixed RAM diagnostic application. Request owner/mode/link/canonical path/inode/hash and single-use checks; native scalar governor/controller options validated and consumed without CPU changes; no arbitrary command loader. Guard-only rehearsal has no UI/app execution. Native cancel and selected app -> core C40 -> launcher qualified separately. Core audio is digital zero; no acoustic game qualification, ROM or BIOS. C45 worker/process owner reused byte-exact after immutable rollback proofs; global mounts/preferences/infra/rootRO/foundation97 preserved, RAM removed and final console page restored. No firmware installation/reboot/token, no original32 change. No ELF/image/blob/preferences copy or fingerprint/key/seed/backup/credential included.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C46 native application evidence frozen:',out)
