#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C47 reports and the original MIT cartridge; exclude emulator ELF/firmware."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/nes-core';out=repo/'dist/phase4/nes-core-content'
assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area));sources={str(Path(__file__).relative_to(repo))}
def copy(src,dst):
 p=public/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
def report(stage,label):
 r=json.loads((stage/'analysis.json').read_text());assert r['passed'],(stage,r)
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h,(stage,n);sources.add(n)
 copy(stage/'analysis.json',label+'/analysis.json');return r
core=Path((area/'latest').read_text().strip());nr=report(core,'core-build')
host=Path((area/'latest-host').read_text().strip());hr=report(host,'host-build')
api=Path((area/'latest-api').read_text().strip());ar=report(api,'core-api');assert ar['build_stage']==str(core)
checks=Path((area/'latest-checks').read_text().strip());cr=report(checks,'host-checks');assert cr['build_stage']==str(host)
assert sha(Path(nr['source_stage'])/'fceumm_libretro.so')==nr['core_sha256']
assert sha(host/'source/bin/muxretro')==hr['binary_sha256']
for stage,label in [(api,'core-api'),(checks,'host-checks')]:
 for ext in ['sh','stdout','stderr','exit']:copy(stage/('check.'+ext),label+'/check.'+ext)
for label,pointer,outcome in [('native-api','latest-cycle','native-guards-only'),('selection','latest-selection','selected-app-returned')]:
 stage=Path((area/pointer).read_text().strip());r=report(stage,label)
 assert r['outcome']==outcome and r['core_sha256']==nr['core_sha256'] and r['ROM_sha256']==nr['ROM_sha256'] and r['host_binary_sha256']==hr['binary_sha256']
 assert r['host_checks_sha256']==sha(checks/'analysis.json')
 assert all(r[n] for n in ['cleanup_passed','global_mountinfo_unchanged','root_ro','RAM_removed']) and not r['preferences_persisted']
 for n in ['intent.json','dispatch.json']:copy(stage/n,label+'/'+n)
 for prefix in ['preflight','prepare','native','postflight','mount-health','cleanup','stopped-screen']:
  for ext in ['sh','stdout','stderr','exit']:copy(stage/(prefix+'.'+ext),label+'/'+prefix+'.'+ext)
 copy(stage/'collected/result.txt',label+'/result.txt')
 for log in ['core.log','dispatch.log','game.log','return.log','nes-api.log']:
  p=stage/'collected'/log
  if p.exists():
   lines=[s for s in p.read_text().splitlines() if re.search(r'^C4[4567]_|^RETRO_RUNNER_',s)]
   (public/label/(log+'.markers')).write_text('\n'.join(lines)+'\n')
 if label=='selection':
  assert 'C47_FIXED_CONTENT_VERIFIED' in (stage/'collected/game.log').read_text()
  assert re.search(r'^C44_NORMAL_EXIT expired=1 frames=[1-9][0-9]*$',(stage/'collected/game.log').read_text(),re.M)
  obs=json.loads((stage/'physical-observation.json').read_text());assert obs['qualified'];copy(stage/'physical-observation.json',label+'/physical-observation.json')
  for n in ['selected-action.txt','selected-application.txt','application-governor.txt','application-controller.txt']:copy(stage/'collected'/n,label+'/'+n)
  for n in ['observation-active.sh','observation-active.stdout']:
   if (stage/n).exists():copy(stage/n,label+'/'+n)
# The only distributed cartridge is original MIT code/artwork; no core binary.
assert sha(core/'r35s-flight.nes')==nr['ROM_sha256']
copy(core/'r35s-flight.nes','original/r35s-flight.nes');copy(core/'r35s-flight.json','original/r35s-flight.json');copy(repo/'port/LICENSE','original/LICENSE')
if nr.get('ROM_parent_stage'):
 parent=Path(nr['ROM_parent_stage']);assert sha(parent/'analysis.json')==nr['ROM_parent_analysis_sha256']
 copy(parent/'analysis.json','history/initial-ROM/analysis.json')
 copy(parent/'r35s-flight.nes','history/initial-ROM/r35s-flight.nes')
 first=area/'observe.5ax7pcci'
 for n in ['analysis.json','physical-observation.json']:copy(first/n,'history/initial-native-content/'+n)
for n in sorted(sources):copy(repo/n,'source/'+n)
(public/'NOTICE.txt').write_text('C47 pinned FCEUmm GPLv2 core built from official source; full source archive and recipe retained privately. Source URL/commit/archive hash recorded in core-build report. No FCEUmm ELF or GPU blob distributed here. Original MIT NROM cartridge/code/artwork only, no commercial ROM/BIOS. Real AArch64/QEMU and native CPU tests verify video/RAM/D-pad/reset/serialize/silence; bounded muxretro native content load and physical selection/input/launcher return separately qualified. Audio content is zero, no music/acoustic qualification. C46 signed worker/UI/adapter reused, RAM-only fixed content, preferences/dataRO+RAM, no governor/sysfs application. RootRO/foundation97/network/infra/mounts/preferences preserved; RAM removed and final page restored. No installation, boot token, reboot, image flash, original32 or Deck changes. No private preferences/fingerprints/backup/key/seed/credential included.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C47 native NES content evidence frozen:',out)
