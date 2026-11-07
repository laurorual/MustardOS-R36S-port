#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C04: real S99 UI, physical confirmation, root/entropy/stock return checks."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
b=Path(sys.argv[1]).resolve();repo=Path(__file__).resolve().parents[2]
u=json.loads((b/'user-confirmation.json').read_text())
assert all(u[name] for name in ['menu_legible_oriented','info_config_help_navigation_passed','diagnostic_returned'])
d=json.loads((b/'log-collection.json').read_text());assert d['experiment']=='MUOS-R35S-FRONTEND-P4-C04'
subprocess.run([sys.executable,str(repo/'port/scripts/analyze-phase4-entropy-boot.py'),str(b),'persisted'],check=True,capture_output=True,text=True)
(b/'analysis.json').replace(b/'entropy-analysis.json')
r=d['files']['REPORT.TXT']['text'];section=r.split('FRONTEND\n',1)[1].split('MAPPING\n',1)[0]
for text in ['UI_WINDOW_STARTED','UI_WINDOW_ENDED','C04_UI_STOPPED=1','STOP reason=stop signal=15','FIRST_PAINT']:
    assert text in section,text
assert 'CHILD hotkey ' not in section and not re.search(r'^EXIT \d+ status=',section,re.M)
identity=re.search(r'UI_ID manager=(\d+) frontend=(\d+) parent=(\d+)',section);assert identity and identity[1]==identity[3]
modules=list(dict.fromkeys(re.findall(r'^UI_MODULE=(\S+)$',section,re.M)))
assert {'muxlaunch','muxinfo','muxconfig'}<=set(modules),modules
before=section.split('DRM_BEFORE\n',1)[1].splitlines()[0]
after=section.split('DRM_AFTER\n',1)[1].splitlines()[0]
assert before==after and 'size=640x480' in before
mounts=r.split('FINAL MOUNTS\n',1)[1]
assert not any(line.split()[1]=='/etc/default/muos-ui' for line in mounts.splitlines())
assert not re.search(r'Could not restore CRTC|segmentation fault|SIGSEGV|first_paint_timeout|input_or_core_lost',section,re.I)
result={'scope':'C04 first supervised frontend cold boot on own kernel, silent/no hotkeys','passed':True,'fresh_first_paint_parent_and_installed_service_verified':True,'observed_modules':modules,'physical_navigation_confirmed':True,'controlled_service_stop_and_drm_mode_restore_passed':True,'temporary_ui_config_unmounted':True,'root_ro_entropy_rotation_input_stop_fsck_stock_return_passed':True,'ui_window_target_seconds':75,'audio_hotkeys_power_network_content_launch_tested':False,'long_term_stability_other_panels_tested':False,'seed_bytes_or_hashes_collected':False,'collection_sha256':hashlib.sha256((b/'log-collection.json').read_bytes()).hexdigest(),'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(b/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
