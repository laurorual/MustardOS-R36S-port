#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C122 sanitized installed package and native zero-upload adoption proof."""
import json,os,shutil,tempfile
from pathlib import Path
import phase4_resident_batch as m
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);out=m.REPO/'dist/phase4/resident-batch-installed';m.require(not out.exists(),'Never replace C122 proof')
 package=Path((m.AREA/'latest-package').read_text().strip());installed=Path((m.AREA/'latest-complete').read_text().strip())
 validated=Path((m.AREA/'latest-validated').read_text().strip());checks=Path((m.AREA/'latest-checks').read_text().strip())
 for p in [package,installed,validated,checks]:m.require(p.resolve().is_relative_to(m.AREA),'Known C122 record')
 pkg=json.loads((package/'analysis.json').read_text());r=json.loads((installed/'analysis.json').read_text())
 v=json.loads((validated/'analysis.json').read_text());c=json.loads((checks/'analysis.json').read_text());plan=json.loads((installed/'plan.json').read_text())
 for row in [pkg,r,v,c]:m.require(row['passed'] is True and row['schema']==122,'Complete C122 qualification')
 m.require(r['plan_sha256']==m.sha(installed/'plan.json') and plan['package_analysis_sha256']==c['package_analysis_sha256']==m.sha(package/'analysis.json'),'Exact C122 package/plan/checks')
 m.require(r['checks_sha256']==m.sha(checks/'analysis.json') and r['files_added']==9 and r['directories_added']==1 and r['existing_files_replaced']==0,'Exact additive install')
 for key in ['root_read_only','RAM_removed','private_state_fingerprint_matched','infrastructure_and_global_mounts_preserved']:
  m.require(r[key] is True,'Incomplete installation: '+key)
 m.require(v['installed_analysis_sha256']==m.sha(installed/'analysis.json') and v['inputs_and_contract_files_uploaded']==0,'Bound zero-upload validation')
 for key in ['exact_C120_bundle_copied_locally','new_run_claim_absent','repeat_and_save_refused','adopted_host_check_passed','global_mounts_and_infrastructure_preserved','RAM_removed','root_readonly']:
  m.require(v[key] is True,'Incomplete validation: '+key)
 m.require(v['GUI_core_audio_input_reboot_or_persistent_write_executed'] is False,'No new graphical qualification')
 for stage,labels in [(installed,['result','after','mounts-private','caller-check','native-stage','cleanup-stage','cleanup','post-cleanup-health']),
  (validated,['before','mounts-before','allocate','prepare','adopt','verify','after','mounts-after','cleanup','post-cleanup-health'])]:
  for n in labels:m.require((stage/(n+'.exit')).read_text()=='0\n','Authentic native receipt')
 m.require((validated/'before.stdout').read_bytes()==(validated/'after.stdout').read_bytes()==(validated/'post-cleanup-health.stdout').read_bytes(),'Validation infrastructure unchanged')
 m.require((validated/'mounts-before.stdout').read_bytes()==(validated/'mounts-after.stdout').read_bytes(),'Validation global mounts unchanged')
 m.require((validated/'adopt.stdout').read_text()=='C122_RESIDENT_BATCH_ADOPTED_ZERO_UPLOADS\n','Native resident adoption')
 sources={Path(__file__),m.REPO/'docs/archive/phase4/phase4-resident-batch.md'}
 for row in [pkg,r,v,c]:
  for name,h in row['source_sha256'].items():
   p=m.REPO/name;m.require(m.sha(p)==h,'Frozen source changed');sources.add(p)
 public=Path(tempfile.mkdtemp(prefix='public.',dir=m.AREA))
 summary={'passed':True,'schema':122,'boot_sequence':r['boot_sequence'],'files_added':9,'directories_added':1,'bytes_added':r['bytes_added'],
 'existing_files_replaced':0,'installed_prefix':m.PREFIX,'native_package_and_incomplete_capsule_refusal_passed':True,
 'zero_upload_resident_copy_and_C120_adoption_passed':True,'runtime_inputs_and_contract_files_uploaded':0,'new_run_claim_absent':True,
 'root_readonly':True,'RAM_removed':True,'private_fingerprint_and_global_mounts_preserved':True,'new_graphical_cycle_qualified':False,
 'autostart_enabled':False,'new_save_or_reboot_requested':False,'ROM_or_ELF_in_package':False,'full_image_generated_or_Deck_used':False,
 'offline_cases':c['case_count'],'source_payload_files':pkg['package_files'],'parent_proofs_sha256':pkg['parent_proofs_sha256']}
 write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
 write_new(public/'checks.json',(json.dumps({k:c[k] for k in ['passed','case_count','cases','real_resident_and_C120_functions','device_or_GUI_executed']},indent=2)+'\n').encode())
 expected_export=''.join(pkg['package_files'][n]+'  '+n+'\n' for n in m.NAMES)
 m.require((package/'export.sha256').read_text()==expected_export,'Exact public recipe export manifest')
 write_new(public/'export.sha256',expected_export.encode())
 for n,h in pkg['package_files'].items():
  p=package/'target'/m.PREFIX/n;m.require(m.sha(p)==h,'Qualified payload changed')
  (public/'payload').mkdir(exist_ok=True);shutil.copyfile(p,public/'payload'/n)
 for n in ['transaction.sh','native.sh']:
  m.require(m.sha(package/n)==pkg['adapter_sha256'][n],'Qualified adapter changed');(public/'adapter').mkdir(exist_ok=True);shutil.copyfile(package/n,public/'adapter'/n)
 for p in sources:
  dst=public/'source'/p.relative_to(m.REPO);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
 private=m.graphics.contract.session.previous.resident.qualified_rom()[1]
 forbidden=[v['kernel_boot_id'].encode(),private['ROM_sha256'].encode()]
 for p in public.rglob('*'):
  m.require(not p.is_symlink(),'No public aliases')
  if p.is_file():
   b=p.read_bytes();m.require(not b.startswith(b'\x7fELF') and not any(x in b for x in forbidden),'Private content in proof')
 write_new(public/'SHA256SUMS',''.join(m.sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
 for p in public.rglob('*'):
  if p.is_file():
   with p.open('rb') as f:os.fsync(f.fileno())
 for p in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(p)
 sync_dir(public);os.rename(public,out);sync_dir(out.parent);print('C122 installed resident batch proof:',out)
if __name__=='__main__':main()
