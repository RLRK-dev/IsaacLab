# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Exclude obsolete outfeed display nodes while replaying the unchanged v05 bank."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
V05 = WORK / "hvjb-line-video-v05-20260923"
V04 = WORK / "hvjb-line-video-v04-20260923"
BANK_SHA = "7702cadf9e412895a14c82d1a6b85a6aa659f2978c22e59ddf16e2714c793a60"
spec = importlib.util.spec_from_file_location("preserved_v04_composition", V04 / "render_review.py")
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)


class Model(view.old.Model):
    """Record old static-node provenance and omit only the obsolete outfeed display."""

    def __init__(self):
        self.static_boxes = []
        self.in_old_out_table = False
        super().__init__()
        self.omissions = []
        self.excluded_columns = []
        for row in self.static_boxes:
            old_frame = row["name"] in {"xyz_post", "xyz_rail"} and row["position"][0] in (2.55, 4.25)
            if old_frame or row["old_out_table"]:
                self.scene.remove_node(row["node"])
                self.omissions.append({key: value for key, value in row.items() if key != "node"})
        assert len(self.omissions) == 11, self.omissions
        for column, (name, node) in enumerate(zip(self.names, self.dynamic, strict=True)):
            if name.startswith("outfeed_") or name == "test_probe":
                self.scene.remove_node(node)
                self.excluded_columns.append(column)
                self.omissions.append({"name": name, "dynamic_column": column})
        assert len(self.excluded_columns) == 8
        assert len(self.omissions) == 19

    def table(self, x, y, width, depth):
        self.in_old_out_table = (x, y, width, depth) == (4.0, -0.1, 1.1, 0.8)
        super().table(x, y, width, depth)
        self.in_old_out_table = False

    def add_box(self, name, dims, mat, pos, dynamic=True):
        node = super().add_box(name, dims, mat, pos, dynamic)
        if not dynamic:
            self.static_boxes.append(
                {
                    "name": name,
                    "dimensions_display_units": list(dims),
                    "position": [float(value) for value in pos],
                    "old_out_table": self.in_old_out_table,
                    "node": self.static[-1],
                }
            )
        return node


def prepare(name, preview):
    source = V05 / "data/concept_display_v05_framed.npz"
    assert view.sha(source) == BANK_SHA
    bank = ROOT / "data/concept_display_v05_reused.npz"
    if not bank.exists():
        shutil.copy2(source, bank)
    assert view.sha(bank) == BANK_SHA
    old_plan = json.loads((V05 / "data/concept_v05.json").read_text())
    assert old_plan["motion_sha256"] == BANK_SHA
    if preview:
        indices = np.array(
            [0, 54, 72, 115, 123, 150, 300, 438, 580, 800, 1100, 1290, 1410, 1515, 1560, 1660, 1702, 1770]
        )
    else:
        indices = np.arange(1785)
    plan = dict(old_plan)
    plan.update(
        authored_motion_kind="unchanged_v05_schematic_bank_with_obsolete_outfeed_display_omitted",
        motion=bank.name,
        motion_sha256=BANK_SHA,
        renderer=str(Path(__file__)),
        frame_end=len(indices) * 2,
        expected_source_samples=[dict(old_plan["expected_source_samples"][int(index)]) for index in indices],
        scope_caption="HVJB 全体工程 v05b｜左：模式動作 / 右：完成状態の部品照合図 / 実機仕様・実タクトは未確定",
        output_name=name,
        preview_only=preview,
        saved_geometry_or_motion_modified=False,
        display_environment_modified=True,
        display_omissions_count=19,
        conditional_lid_omission="Before video 103 s; lid placement and fastening are unspecified",
        product_geometry_and_motion_modified=False,
        original_v05_plan_sha256=view.sha(V05 / "data/concept_v05.json"),
    )
    extra = [
        Path(__file__),
        ROOT / "REVIEW_SCOPE.md",
        V04 / "render_review.py",
        WORK / "hvjb-logistics-review-v01-20260923/audit/logistics_observations.json",
        bank,
    ]
    plan["input_sha256"] = {**old_plan["input_sha256"], **{str(path): view.sha(path) for path in extra}}
    return bank, plan, indices


def render(bank, plan, indices, directory):
    with np.load(bank, allow_pickle=False) as saved:
        matrices, cameras, spans, times, names = [
            saved[key] for key in ("matrices", "camera", "span", "time_s", "object_names")
        ]
    model = Model()
    assert model.names == names.tolist()
    composition = view.Composition(json.loads((view.DOCUMENT / "data/line_review_data.json").read_text()))
    renderer = view.old.base.pyrender.OffscreenRenderer(view.old.WIDTH, view.old.HEIGHT)
    rows = []
    try:
        for number, index in enumerate(indices):
            png = directory / f"{number + 1:05d}.png"
            for column, (node, pose) in enumerate(zip(model.dynamic, matrices[index], strict=True)):
                if column not in model.excluded_columns:
                    if names[column] == "lid" and times[index] < 103:
                        pose = view.old.base.transform(view.old.base.HIDDEN)
                    model.scene.set_pose(node, pose)
            model.scene.set_pose(model.camera, cameras[index])
            model.camera.camera.xmag = spans[index]
            model.camera.camera.ymag = spans[index] * view.old.HEIGHT / view.old.WIDTH
            color, depth = renderer.render(model.scene)
            assert np.isfinite(depth).all() and np.count_nonzero(depth) > 1000
            points = {name: matrices[index, model.names.index(name + "_palm"), :3, 3] for name in model.arms}
            composition.compose(color, float(times[index]), cameras[index], spans[index], points).save(png)
            rows.append(
                dict(
                    plan["expected_source_samples"][number],
                    view="process",
                    frame=number * 2 + 1,
                    camera=plan["camera"],
                    file=png.name,
                    sha256=view.sha(png),
                    display_segment="saved_sample",
                    original_sample_index=int(index),
                )
            )
            if number % 60 == 0 or number == len(indices) - 1:
                print(f"V05B_PROCESS_PNG {number + 1}/{len(indices)}", flush=True)
    finally:
        renderer.delete()
    return rows, model.omissions, len(composition.text_bounds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output_name", default="concept_v05b")
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name
    directory = ROOT / "previews" / args.output_name
    plan_path = ROOT / "data" / f"{args.output_name}.json"
    assert not directory.exists() and not plan_path.exists()
    for folder in ("data", "previews", "audit"):
        (ROOT / folder).mkdir(exist_ok=True)
    bank, plan, indices = prepare(args.output_name, args.preview)
    for path, digest in plan["input_sha256"].items():
        assert view.sha(Path(path)) == digest, path
    view.save(plan_path, plan)
    directory.mkdir()
    rows, omissions, text_count = render(bank, plan, indices, directory)
    for path, digest in plan["input_sha256"].items():
        assert view.sha(Path(path)) == digest, path
    view.save(
        directory / "manifest.json",
        {
            "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "complete": True,
            "source_kind": plan["source_kind"],
            "output_fps": 15,
            "settings": {"width": 1920, "height": 1080},
            "shot_plan_sha256": view.sha(plan_path),
            "renderer_sha256": view.sha(Path(__file__)),
            "input_sha256_current": plan["input_sha256"],
            "images": rows,
            "display_nodes_omitted": omissions,
            "lid_hidden_before_video_s": 103,
            "saved_bank_identical_to_v05": view.sha(bank) == BANK_SHA,
            "text_elements_checked": text_count,
            "physical_acceptance_verdict": None,
        },
    )
    print(f"V05B_PROCESS_COMPLETE frames={len(rows)} display_nodes_omitted={len(omissions)} bank_unchanged=True")


if __name__ == "__main__":
    main()
