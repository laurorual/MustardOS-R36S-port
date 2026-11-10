#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C113 sanitized receipt only; ROM and backup bytes never enter dist."""
import json,os,shutil,tempfile
from phase4_internal_rom import *
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);out=REPO/'dist/phase4/internal-rom-imported';require(not out.exists(),'Frozen proof must not be replaced')
 stage=Path((AREA/'latest-complete').read_text().strip());require(stage.resolve().is_relative_to(AREA),'Known import')
 r=json.loads((stage/'analysis.json').read_text());tested=json.loads(Path((AREA/'latest-checks').read_text().strip()).joinpath('analysis.json').read_text())
 require(r['passed'] is True and r['schema']==113 and tested['passed'] is True,'Completed import and checks')
 for k in ['private_ROM_internal','existing_data_files_preserved','C109_snapshot_byte_identical','root_read_only','data_unmounted','RAM_removed','global_mountinfo_and_infrastructure_preserved']:require(r[k] is True,'Complete private import')
 require(r['plan_sha256']==sha(stage/'plan.json') and r['independent_backup_sha256']==sha(stage/'before.tar'),'Independent backup/plan')
 for label in ['inspect','native-sync-ABI','dispatch','result','verify','after','mount-health','cleanup','post-cleanup-health']:
  require((stage/(label+'.exit')).read_text()=='0\n','Authentic successful native receipt')
 require((stage/'result.stdout').read_text()=='0\nC113_ROM_INTERNAL_IMPORTED_RO_VERIFIED\nC113_END operation=apply status=0\n','Successful writer')
 public=Path(tempfile.mkdtemp(prefix='public.',dir=AREA));summary={k:v for k,v in r.items() if k not in ['ROM_sha256','kernel_boot_id']}
 summary.update(private_ROM_or_backup_ELF_seed_identity_included=False,redistribution_approved=False,graphical_qualification=False)
 write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
 write_new(public/'checks.json',(json.dumps({k:tested[k] for k in ['passed','case_count','cases','private_content_used','real_media_or_namespace_used','sync_helper_A35_QEMU_used','power_loss_tested']},indent=2)+'\n').encode())
 paths=[REPO/n for n,h in r['source_sha256'].items()]+[Path(__file__),REPO/'docs/archive/phase4/phase4-internal-rom.md']
 for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Qualified source changed')
 for p in paths:
  dest=public/'source'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 for p in public.rglob('*'):
  if p.is_file():require(not p.is_symlink() and not p.read_bytes().startswith(b'\x7fELF') and all(s.encode() not in p.read_bytes() for s in [r['ROM_sha256'],r['kernel_boot_id']]),'No private payload')
 write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
 for p in public.rglob('*'):
  if p.is_file():
   with p.open('rb') as f:os.fsync(f.fileno())
 sync_dir(public);os.rename(public,out);sync_dir(out.parent);print('C113 sanitized import proof:',out)
if __name__=='__main__':main()
