# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Keep unknown-work banners clear without changing the saved display motion."""

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import render_process as display

ROOT = Path(__file__).resolve().parent


def main():
    source_plan = ROOT / "data/concept_v03.json"
    source_folder = ROOT / "previews/concept_v03"
    source_manifest_path = source_folder / "manifest.json"
    plan = json.loads(source_plan.read_text())
    source_manifest = json.loads(source_manifest_path.read_text())
    assert source_manifest["complete"]
    assert source_manifest["shot_plan_sha256"] == display.sha(source_plan)
    assert all(display.sha(path) == digest for path, digest in plan["input_sha256"].items())
    final_folder = ROOT / "previews/concept_v03_final"
    final_plan = ROOT / "data/concept_v03_final.json"
    assert not final_folder.exists() and not final_plan.exists()
    final_folder.mkdir()
    plan["renderer"] = str(Path(__file__))
    for path in [Path(__file__), source_plan, source_manifest_path]:
        plan["input_sha256"][str(path)] = display.sha(path)
    plan["label_refinement"] = dict(
        scenes=["S09", "S13"],
        change="Do not place role labels over the unknown-work banner.",
        source_plan_sha256=display.sha(source_plan),
        geometry_or_motion_changed=False,
    )
    display.save(final_plan, plan)
    original_labels = display.role_labels

    def clear_unknown_labels(draw, row, camera, span, points):
        if row["id"] not in {"S09", "S13"}:
            original_labels(draw, row, camera, span, points)

    display.role_labels = clear_unknown_labels
    model = display.Model()
    renderer = display.base.pyrender.OffscreenRenderer(display.WIDTH, display.HEIGHT)
    cache, rows, changed = {}, [], []
    try:
        with np.load(ROOT / "data" / plan["motion"], allow_pickle=False) as bank:
            for i, source_row in enumerate(source_manifest["images"]):
                source = source_folder / source_row["file"]
                assert display.sha(source) == source_row["sha256"]
                target = final_folder / source.name
                row = dict(source_row)
                if row["feature_id"] in {"S09", "S13"}:
                    payload = bank["matrices"][i].tobytes() + bank["camera"][i].tobytes() + bank["span"][i].tobytes()
                    key = (row["feature_id"], hashlib.sha256(payload).hexdigest())
                    if key not in cache:
                        for node, pose in zip(model.dynamic, bank["matrices"][i]):
                            model.scene.set_pose(node, pose)
                        model.scene.set_pose(model.camera, bank["camera"][i])
                        model.camera.camera.xmag = bank["span"][i]
                        model.camera.camera.ymag = bank["span"][i] * display.HEIGHT / display.WIDTH
                        color, depth = renderer.render(model.scene)
                        assert np.isfinite(depth).all()
                        points = {n: bank["matrices"][i, model.names.index(n + "_palm"), :3, 3] for n in model.arms}
                        cache[key] = display.label_image(
                            color, float(bank["time_s"][i]), bank["camera"][i], bank["span"][i], points
                        )
                    cache[key].save(target)
                    changed.append(row["frame"])
                else:
                    shutil.copy2(source, target)
                row["pre_refinement_png_sha256"] = row["sha256"]
                row["sha256"] = display.sha(target)
                rows.append(row)
    finally:
        renderer.delete()
    assert all(display.sha(path) == digest for path, digest in plan["input_sha256"].items())
    final_manifest = dict(
        source_manifest,
        images=rows,
        shot_plan_sha256=display.sha(final_plan),
        renderer_sha256=display.sha(__file__),
        input_sha256_current=plan["input_sha256"],
    )
    final_manifest["label_refinement"] = dict(
        plan["label_refinement"],
        redrawn_frames=len(changed),
        unique_static_images=len(cache),
        original_manifest_sha256=display.sha(source_manifest_path),
    )
    display.save(final_folder / "manifest.json", final_manifest)
    display.save(ROOT / "audit/label_refinement.json", final_manifest["label_refinement"])
    print("LABEL_REFINEMENT_COMPLETE", len(rows), "redrawn", len(changed), "unique", len(cache), flush=True)


if __name__ == "__main__":
    main()
