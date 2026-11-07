#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C109 retain C77 evidence checks and add sampled selection-to-present timing."""
from pathlib import Path
import argparse,json,re,subprocess,sys
from phase4_candidate import sha
from phase4_root_migration import require

def timing_metrics(watch,game):
    values={}
    for phase in ['selection_consumed','first_game_present']:
        rows=re.findall(r'^C109_EVENT '+phase+r' uptime=([0-9]+[.][0-9]+)$',watch,re.M)
        require(len(rows)==1,'Exactly one observed timing event '+phase);values[phase]=float(rows[0])
    delay=values['first_game_present']-values['selection_consumed']
    require(0<=delay<=120,'Ordered bounded selection-to-present observations')
    startup=re.findall(r'Startup: ready in ([0-9]+[.][0-9]+) ms total',game)
    require(len(startup)==1,'One native startup measurement')
    return {'observed_selection_to_present_seconds':round(delay,3),'watch_nominal_sampling_seconds':1,
        'watch_scheduler_delay_bounded':False,'physical_button_timestamp_measured':False,
        'core_reported_startup_ms':float(startup[0]),'timing_event_pair_valid':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',type=Path);args=parser.parse_args()
    repo=Path(__file__).resolve().parents[2];stage=args.stage.resolve()
    require(stage.is_relative_to(repo/'build/phase4/prepared-capsule-session'),'Known C109 stage')
    source=repo/'port/scripts/analyze-phase4-installed-core-session.py'
    frozen=repo/'dist/phase4/installed-core-session/source'/source.relative_to(repo)
    require(source.read_bytes()==frozen.read_bytes(),'Frozen C77 analyzer')
    subprocess.run([sys.executable,'-B',str(source),str(stage)],check=True)
    path=stage/'technical-analysis.json';r=json.loads(path.read_text())
    r.update(timing_metrics((stage/'watch-maps.stdout').read_text(),(stage/'collected/game.log').read_text()))
    r['C109_local_preparation_analyzed']=True;r['source_sha256'][str(Path(__file__).relative_to(repo))]=sha(Path(__file__))
    path.write_text(json.dumps(r,indent=2)+'\n')
    print('C109 sampled selection-to-present:',r['observed_selection_to_present_seconds'],'s; core startup:',r['core_reported_startup_ms'],'ms')

if __name__=='__main__':main()
