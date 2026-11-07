#!/usr/bin/env bash
# Package a checked local candidate, including license/source material.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/menu/active" ]] || { echo "Menu profile owns the mutable graphics output; use its controllers." >&2; exit 1; }
candidate="$work/graphics-config"
output="$repo/dist/phase4/graphics-candidate"
for stage in build audit legal-info; do [[ $(cat "$candidate/$stage.exit") == 0 ]]; done
for job in muos-r35s-phase4-graphics muos-r35s-phase4-graphics-legal; do
    [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]
done
python3 - "$repo" "$candidate" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,candidate=map(Path,sys.argv[1:]);m=json.loads((candidate/'audit/host-audit.json').read_text())
for name,sha in m['input_sha256'].items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha,name
for name,sha in json.loads((candidate/'report.json').read_text()).get('global_patch_sha256',{}).items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha,name
assert (candidate/'output/.config').read_bytes()==(candidate/'output/legal-info/buildroot.config').read_bytes(), 'Recollect legal-info for the current configuration'
assert (candidate/'report.json').read_bytes()==(candidate/'output/legal-info/port-input-report.json').read_bytes(), 'Recollect legal-info for the current patch set'
with (candidate/'output/images/rootfs.ext4').open('rb') as f:
    assert hashlib.file_digest(f,'sha256').hexdigest()==m['rootfs']['ext4']['sha256']
PY
mkdir -p "$output"
cp --reflink=auto --sparse=always "$candidate/output/images/rootfs.ext4" "$output/"
cp "$candidate/audit/"* "$output/"
cp "$candidate/report.json" "$output/config-report.json"
cp "$candidate/core-source-manifest.json" "$output/"
cp "$candidate/output/.config" "$output/buildroot.config"
cp -a --reflink=auto "$candidate/output/legal-info" "$output/"
cp "$candidate/provider-source/source-files.json" "$output/provider-source-files.json"
if [[ -f "$candidate/native-result.json" ]]; then
    cp "$candidate/native-result.json" "$candidate/native-run.log" "$output/"
    native=$(cat "$candidate/latest-native-session")
    [[ $native == "$candidate/"native-session.* && -f "$native/remote-session" ]]
    cp -a --reflink=auto "$native" "$output/native-session"
fi
tar -C "$repo" --exclude=__pycache__ --exclude='*.pyc' -czf "$output/port-source.tar.gz" port
printf '%s\n' 'EXPERIMENTAL GRAPHICS ROOTFS; NOT A FLASHABLE FIRMWARE.' \
    'Host/QEMU checks do not validate the Mali kernel interface or a physical display.' \
    'Full muOS init/frontend, boot chain and native runtime validation remain open.' > "$output/NOT-FOR-DEVICE-BOOT.txt"
python3 - "$work" "$output" <<'PY'
from pathlib import Path
import hashlib,json,sys
work,out=map(Path,sys.argv[1:])
m={'purpose':'separate graphics candidate; private host bring-up',
   'buildroot_revision':'4f924fd52841608d68ac3dcb83fccee8b8c90316',
   'container_image_id':(work/'rootfs-container.iid').read_text().strip(),
   'host_audit':json.loads((out/'host-audit.json').read_text()),
   'native_graphics_tested':False,'native_audio_tested':False,'native_input_tested':False,
   'boot_tested':False,'full_muos_sysinit':False,'frontend_integrated':False,
   'legal_info_collected':True,'distribution_with_gpl_frontend_reviewed':False}
if (out/'native-result.json').exists():
 r=json.loads((out/'native-result.json').read_text())
 assert r['rootfs_sha256']==m['host_audit']['rootfs']['ext4']['sha256']
 m.update(native_graphics_tested=True,native_graphics_passed=r['native_graphics_passed'],native_result=r)
(out/'build-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(out/'legal-info/PORT-SUPPLEMENT.txt').write_text('Buildroot source is supplied in buildroot-source.tar.gz despite the generated README warning.\nLocal muos-core source is supplied in sources/muos-core-1/muos-core-1.tar.gz.\nPort recipes, patches and probes are in ../port-source.tar.gz.\nThe proprietary Mali library retains its specific EULA and notices; this local candidate is not publication approval.\n')
with (out/'SHA256SUMS').open('w') as sums:
 for p in sorted(out.rglob('*')):
  if p.is_file() and p.name!='SHA256SUMS':
   with p.open('rb') as f: h=hashlib.file_digest(f,'sha256').hexdigest()
   sums.write(f'{h}  {p.relative_to(out)}\n')
PY
echo "Checked local candidate packaged: $output"
