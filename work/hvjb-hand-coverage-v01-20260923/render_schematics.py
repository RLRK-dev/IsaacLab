# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Display five existing dimensionless hand drawings without changing their geometry."""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = ROOT / "sources/legacy_finger_drawings.py.txt"
    identity = json.loads((ROOT / "source_identity.json").read_text())
    record = next(row for row in identity["files"] if row["copy"] == str(source.relative_to(ROOT)))
    assert sha(source) == record["sha256"]
    loader = importlib.machinery.SourceFileLoader("hvjb_preserved_drawings", str(source))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    outputs = []
    for identifier in ("H01", "H02", "H03", "H07", "H08"):
        destination = ROOT / "figures" / f"{identifier}_schematic.png"
        assert not destination.exists(), destination
        fig = module.plt.figure(figsize=(9.6, 6.6), dpi=100, facecolor="white")
        ax = fig.add_axes([0.04, 0.05, 0.92, 0.91])
        ax.set(xlim=(0, 100), ylim=(0, 70))
        ax.set_aspect("equal")
        ax.axis("off")
        getattr(module, "draw_" + identifier.lower())(ax)
        label_moves = {"片側の基準面": (2, 4), "長手端当て": (46, 4), "胴の把持可能面を使う": (9, 58)}
        for text in ax.texts:
            if text.get_text() in label_moves:
                text.set_position(label_moves[text.get_text()])
                text.set_ha("left")
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bounds = []
        for text in ax.texts:
            box = text.get_window_extent(renderer)
            bounds.append({"text": text.get_text(), "bounds_px": list(box.extents)})
            assert box.x0 >= 0 and box.y0 >= 0 and box.x1 <= 960 and box.y1 <= 660, bounds[-1]
        fig.savefig(destination, dpi=100, facecolor="white")
        module.plt.close(fig)
        outputs.append(
            {
                "id": identifier,
                "file": str(destination.relative_to(ROOT)),
                "sha256": sha(destination),
                "text_bounds": bounds,
                "label_positions_adjusted": identifier in {"H02", "H08"},
            }
        )
    assert sha(source) == record["sha256"]
    result = {
        "source_sha256": sha(source),
        "outputs": outputs,
        "schematic_dimensions_selected": False,
        "source_geometry_changed": False,
        "renderer_sha256": sha(Path(__file__)),
    }
    (ROOT / "schematic_receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("HAND_SCHEMATICS_COMPLETE figures=5", flush=True)


if __name__ == "__main__":
    main()
