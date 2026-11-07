#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package a RAM-only module-unload-before-reboot experiment for C07r3."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=Path((work/'linux-diagnostic/latest-network-recovery').read_text().strip());meta=json.loads((base/'manifest.json').read_text())
fixtures=Path((work/'network-tools/latest-unload-hooks').read_text().strip());checks=json.loads((fixtures/'report.json').read_text());assert checks['passed'] and len(checks['cases'])==7
stage=Path(tempfile.mkdtemp(prefix='network-unload.',dir=work/'linux-diagnostic'));pkg=stage/'package';pkg.mkdir()
shutil.copyfile(repo/'port/device/rk-r35s-p0/network-driver-diagnostic/run.sh',pkg/'run.sh')
required={**meta['unchanged_required'],**{e['path']:e['sha256'] for e in meta['entries']}}
(pkg/'prerequisites.sha256').write_text(''.join(v+'  /'+n+'\n' for n,v in sorted(required.items())))
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:ro,z',
 (work/'rootfs-container.iid').read_text().strip(),'qemu-aarch64','-cpu','cortex-a35','-L','/work/'+str((base/'extracted').relative_to(work)), '/work/'+str((base/'extracted/bin/busybox').relative_to(work)),'sh','-n','/work/'+str((pkg/'run.sh').relative_to(work))]
r=subprocess.run(args,capture_output=True,text=True,timeout=30);(stage/'shell.stdout').write_text(r.stdout);(stage/'shell.stderr').write_text(r.stderr);assert r.returncode==0
(pkg/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(pkg.iterdir())))
with tarfile.open(stage/'deployment.tar','w') as t:
 for p in pkg.iterdir():t.add(p,arcname=p.name)
record={'experiment':'C07 temporary module-unload-before-normal-reboot','host_passed':True,'native_tested':False,'persistent_boot_code_changed':False,'root_changes':False,'source_sha256':sha(repo/'port/device/rk-r35s-p0/network-driver-diagnostic/run.sh'),'preparer_sha256':sha(Path(__file__)),'base_manifest_sha256':sha(base/'manifest.json'),'deployment_sha256':sha(stage/'deployment.tar'),'fixtures':checks,'fixture_report_sha256':sha(fixtures/'report.json'),'secrets_included':False}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-network-unload').write_text(str(stage)+'\n');print('Unload-reboot RAM package passed:',stage)
