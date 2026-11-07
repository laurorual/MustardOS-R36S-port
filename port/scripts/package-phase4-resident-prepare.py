#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C114 sanitized automatic preparation evidence; no graphical qualification."""
import json,os,shutil,tempfile
from phase4_resident_runtime import *
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);out=REPO/'dist/phase4/resident-preparation';require(not out.exists(),'Do not replace frozen proof')
 stage=Path((AREA/'latest-complete').read_text().strip());require(stage.resolve().is_relative_to(AREA),'Known C114 validation')
 r=json.loads((stage/'analysis.json').read_text())
 require(r['passed'] is True and r['schema']==114 and r['inputs_uploaded']==0 and
   r['GUI_core_input_audio_or_reboot_executed'] is False and r['local_ROM_reads_prohibited'] is True,'True resident preparation only')
 for k in ['ROM_internal_p3_verified','identity_and_metadata_match_C109','native_eager_ABI_and_host_CLI_passed',
  'root_read_only','data_unmounted','RAM_removed','global_mountinfo_and_infrastructure_preserved']:require(r[k] is True,'C114 complete')
 for label in ['before','prepare','validate','host-cli','provider-ABI','after','mounts-after','cleanup','post-cleanup-health']:
  require((stage/(label+'.exit')).read_text()=='0\n','Successful native receipt')
 require((stage/'before.stdout').read_bytes()==(stage/'after.stdout').read_bytes()==(stage/'post-cleanup-health.stdout').read_bytes(),'Infrastructure unchanged')
 public=Path(tempfile.mkdtemp(prefix='public.',dir=AREA));summary={k:v for k,v in r.items() if k!='kernel_boot_id'}
 summary.update(private_ROM_ELF_seed_snapshot_or_backup_included=False,redistribution_approved=False)
 write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
 for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C114 source changed')
 for p in [REPO/n for n in r['source_sha256']]+[Path(__file__),REPO/'docs/analysis/phase4-resident-preparation.md']:
  dest=public/'source'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 for p in public.rglob('*'):
  if p.is_file():require(not p.is_symlink() and not p.read_bytes().startswith(b'\x7fELF') and r['kernel_boot_id'].encode() not in p.read_bytes(),'No runtime private identity/payload')
 write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
 for p in public.rglob('*'):
  if p.is_file():
   with p.open('rb') as f:os.fsync(f.fileno())
 sync_dir(public);os.rename(public,out);sync_dir(out.parent);print('C114 sanitized automatic resident preparation:',out)
if __name__=='__main__':main()
