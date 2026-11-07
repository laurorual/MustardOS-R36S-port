#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze the C47 wall-throughput/buffer finding separately from functional success."""
from pathlib import Path
import json,re,tempfile,shutil
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/nes-core';stage=Path((area/'latest-selection').read_text().strip());text=(stage/'collected/game.log').read_text()
seconds=int(re.search(r'^C44_FIRST_PRESENT seconds=(\d+)',text,re.M).group(1));frames=int(re.search(r'^C44_NORMAL_EXIT expired=1 frames=(\d+)',text,re.M).group(1))
underruns=re.findall(r'Audio ring underran (\d+) time',text)
report={'functional_session_passed':True,'performance_qualified':False,'stage':str(stage),'deadline_seconds':seconds,'emulated_frames':frames,'approximate_frames_per_deadline_second':frames/seconds,'nominal_NES_fps':60.099827,'audio_ring_underruns':int(underruns[-1]) if underruns else None,'interpretation':'Nominal content-rate metadata is not measured wall throughput. No acoustic/music qualification; ROM is digital silence. Cause not isolated; profile loop/render/audio before claiming full speed.','source_sha256':{str(Path(__file__).relative_to(repo)):sha(Path(__file__))},'game_log_sha256':sha(stage/'collected/game.log')}
out=repo/'dist/phase4/nes-core-performance-observation';assert not out.exists();public=Path(tempfile.mkdtemp(prefix='performance-public.',dir=area))
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(public/'markers.txt').write_text('\n'.join(s for s in text.splitlines() if re.search(r'^C44_|Audio ring underran|Audio rate control settled|Content rate locked',s))+'\n')
shutil.copyfile(Path(__file__),public/Path(__file__).name)
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(public.iterdir()) if p.is_file()))
shutil.move(public,out);print('C47 performance observation frozen:',json.dumps(report))
