#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check C03 public boot logs plus explicit physical confirmation."""
from pathlib import Path
import hashlib,json,re,subprocess,sys

folder=Path(sys.argv[1]).resolve();repo=Path(__file__).resolve().parents[2]
confirmation=json.loads((folder/'user-confirmation.json').read_text())
assert confirmation['quadrants_orientation_motion_correct'] and confirmation['diagnostic_text_returned']
d=json.loads((folder/'log-collection.json').read_text())
assert d['experiment']=='MUOS-R35S-GRAPHICS-P4-C03'
subprocess.run([sys.executable,str(repo/'port/scripts/analyze-phase4-entropy-boot.py'),str(folder),'persisted'],check=True,capture_output=True,text=True)
(folder/'analysis.json').replace(folder/'entropy-analysis.json')
report=d['files']['REPORT.TXT']['text'];log=d['files']['DMESG.TXT']['text']
g=report.split('GRAPHICS\n',1)[1].split('MAPPING\n',1)[0]
for needle in ['EGL_CONTEXT_READBACK_EXIT_STATUS=0','video_driver=KMSDRM','renderer=opengles2','output_size=640x480','readback_red_pixel=PASS','render_failures=0','sdl_probe_exit_status=0','SDL_COMMAND_STATUS=0','DRM_MODE_RESTORED=1','C03_GRAPHICS_STATUS=0']:
    assert needle in g,needle
assert 'Mali-G31' in g and 'r13p0' in g
pixel=re.search(r'readback_rgba=(\d+),(\d+),(\d+),(\d+) gl_error=0x0',g);assert pixel
assert all(abs(int(value)-expected)<=1 for value,expected in zip(pixel.groups(),[32,128,191,255]))
before=g.split('DRM_BEFORE\n',1)[1].split('EGL_BEGIN\n',1)[0].strip()
after=g.split('DRM_AFTER\n',1)[1].split('DRM_MODE_RESTORED=1',1)[0].strip()
assert before==after and 'size=640x480' in before
metrics={}
for name in ['frames','elapsed_seconds','average_fps','frame_interval_median_ms','frame_interval_p95_ms']:
    value=re.search(r'^'+name+r'=([0-9.]+)$',g,re.M);assert value,name
    metrics[name]=float(value[1])
assert metrics['frames']>=2 and 27<=metrics['elapsed_seconds']<=40
fault_pattern=r'mali.*(?:fault|error|timeout|timed out)|gpu.*(?:fault|timeout|timed out)|drm.*(?:timeout|timed out)|Could not restore CRTC'
faults=[line for line in (log+'\n'+g).splitlines() if re.search(fault_pattern,line,re.I)]
assert not faults,faults
result={'scope':'one C03 cold boot on own kernel, EGL pixel readback + 30s SDL KMSDRM, physical confirmation, controlled stop and stock return','passed':True,'metrics':metrics,'egl_readback_passed':True,'sdl_gles2_accelerated_vsync_readback_passed':True,'physical_orientation_colors_motion_confirmed':True,'crtc_mode_before_after_equal':True,'diagnostic_console_visibly_restored':True,'selected_services_stopped_root_ro_fsck_stock_health_passed':True,'persisted_entropy_regression_passed':True,'graphics_fault_pattern':fault_pattern,'graphics_fault_matches':faults,'frontend_audio_events_network_shutdown_tested':False,'other_panels_tested':False,'proprietary_provider_redistribution_approved':False,'long_term_stability_tested':False,'seed_bytes_or_hashes_collected':False,'collection_sha256':hashlib.sha256((folder/'log-collection.json').read_bytes()).hexdigest(),'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(folder/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
