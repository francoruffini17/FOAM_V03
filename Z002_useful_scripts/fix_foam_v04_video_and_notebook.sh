#!/usr/bin/env bash
# Correct the copied video name and install the SIM_6000--6049 notebook.
set -euo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_dir="/Disk_F/FOAM_V04"
notebook_source="/tmp/SIM_6000s_eigenvalue_vs_strain.ipynb"

[[ -d "$target_dir" ]] || { echo "Missing $target_dir" >&2; exit 1; }
[[ -s "$notebook_source" ]] || { echo "Missing $notebook_source" >&2; exit 1; }

old_properties="$target_dir/F001_Video_properties_files/Video_properties_32003.py"
new_properties="$target_dir/F001_Video_properties_files/Video_properties_3200.py"
if [[ -f "$old_properties" ]]; then
    mv "$old_properties" "$new_properties"
fi
cp "$source_dir/F001_Video_properties_files/Video_properties_3200.py" "$new_properties"
cp "$source_dir/docs/SIM_6000_6040_LITE_REFINED.md" "$target_dir/docs/"

old_videos="$target_dir/I002_Videos/Video_32003"
new_videos="$target_dir/I002_Videos/Video_3200"
if [[ -d "$old_videos" && ! -e "$new_videos" ]]; then
    mv "$old_videos" "$new_videos"
fi
mkdir -p "$new_videos" "$target_dir/Z001_Results_Analizer"
for sim in $(seq 6000 6049); do
    mkdir -p "$new_videos/SIM_${sim}"
done
cp "$notebook_source" "$target_dir/Z001_Results_Analizer/"

python3 - "$target_dir/docs/CODEMAP.md" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace('Video_properties_32003.py', 'Video_properties_3200.py')
text = text.replace('Video_32003/', 'Video_3200/')
text += '\n- `Z001_Results_Analizer/SIM_6000s_eigenvalue_vs_strain.ipynb`: eigenvalue, crossing, and `f` analysis for all five families.\n'
path.write_text(text)
PY

echo 'Corrected FOAM_V04 to Video 3200 and installed the SIM_6000--6049 notebook.'
