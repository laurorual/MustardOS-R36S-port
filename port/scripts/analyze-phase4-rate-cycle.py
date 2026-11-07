#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read C32 PCM samples; never infer a rate across a restarted PCM trigger."""
from pathlib import Path
import argparse,json,re

def point(text):
    return {'tstamp':float(re.search(r'tstamp\s+: ([0-9.]+)',text)[1]),
            'trigger':float(re.search(r'trigger_time\s*: ([0-9.]+)',text)[1]),
            'hw_ptr':int(re.search(r'hw_ptr\s+: (\d+)',text)[1]),
            'owner_pid':int(re.search(r'owner_pid\s+: (\d+)',text)[1]),
            'declared_rate':int(re.search(r'^rate: (\d+)',text,re.M)[1])}

def compare(first,second):
    dt=second['tstamp']-first['tstamp'];df=second['hw_ptr']-first['hw_ptr']
    stable=(first['trigger']==second['trigger'] and first['owner_pid']==second['owner_pid']
            and first['declared_rate']==second['declared_rate'] and dt>0 and df>0)
    return {'same_PCM_generation':stable,'first':first,'second':second,
            'frames_per_second':df/dt if stable else None,
            'ratio_to_declared':df/dt/first['declared_rate'] if stable else None}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path,required=True)
    args=parser.parse_args();stage=args.stage.resolve()
    area=Path(__file__).resolve().parents[2]/'build/phase4/audio-buffers'
    assert stage.is_relative_to(area)
    text=(stage/'rate-cycle.stdout').read_text();labels=['BEFORE_FIRST','BEFORE_SECOND','RATE48000_FIRST','RATE48000_SECOND','RESTORED_FIRST','RESTORED_SECOND']
    points={}
    for i,label in enumerate(labels):
        section=text.split(label+'\n',1)[1]
        if i+1<len(labels):section=section.split(labels[i+1]+'\n',1)[0]
        points[label]=point(section)
    results={name:compare(points[a],points[b]) for name,a,b in [
        ('before','BEFORE_FIRST','BEFORE_SECOND'),('forced48000','RATE48000_FIRST','RATE48000_SECOND'),
        ('restored','RESTORED_FIRST','RESTORED_SECOND')]}
    assert json.loads((stage/'rate-cycle-result.json').read_text())['completed']
    # The real trace also contains a misleading positive pointer delta after
    # recovery; changed trigger_time still invalidates that measurement.
    control=points['BEFORE_FIRST'];same=dict(control,tstamp=control['tstamp']+2,hw_ptr=control['hw_ptr']+88200)
    assert compare(control,same)['frames_per_second']==44100
    restarted=dict(same,trigger=control['trigger']+1)
    assert compare(control,restarted)['frames_per_second'] is None
    report={'diagnostic_completed':True,'audio_recovered':False,'audio_qualified':False,
        'rates':results,'force_rate_zero_restored':"key:'clock.force-rate' value:'0'" in text.split('C32_RATE_CYCLE_COMPLETE',1)[1],
        'PCM_restart_invalidates_rate_estimate':True,'no_permanent_change':True}
    (stage/'rate-cycle-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({name:{k:v for k,v in value.items() if k not in ['first','second']} for name,value in results.items()},indent=2))

if __name__=='__main__':main()
