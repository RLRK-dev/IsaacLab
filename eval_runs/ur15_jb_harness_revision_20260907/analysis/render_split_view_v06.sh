#!/usr/bin/env bash
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
set -euo pipefail

split_view=${1:?Expected process or wide}
split_sha=${2:?Expected the final pinned native SHA256}
split_root=/home/rlrk/IsaacLab/eval_runs/ur15_jb_harness_revision_20260907
split_width=1280
if [[ "$split_view" == wide ]]; then
    split_width=960
elif [[ "$split_view" != process ]]; then
    exit 2
fi
[[ "$split_sha" =~ ^[0-9a-f]{64}$ ]]
split_actual=$(sha256sum "$split_root/UR15_JB_OP030_split_v06.blend")
[[ "${split_actual%% *}" == "$split_sha" ]]

/home/rlrk/.local/opt/blender-4.5.13-linux-x64/blender \
    --background --threads 16 --python-exit-code 1 \
    --python "$split_root/scripts/render_op030_v02.py" -- \
    --blend UR15_JB_OP030_split_v06.blend \
    --output_folder "op030_split_${split_view}_v06" \
    --views "$split_view" --video --resume \
    --shot_plan op030_split_shots_v06.json \
    --width "$split_width" --samples 16 --engine CYCLES \
    2>&1 | gzip -1 >> "$split_root/audit/op030_split_${split_view}_v06_render.log.gz"

printf '%s\n' "$split_sha" > "$split_root/audit/op030_split_${split_view}_v06_render_finished"
