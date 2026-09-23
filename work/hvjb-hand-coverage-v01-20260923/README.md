# HVJB hand-to-job coverage — 2026-09-23

This review joins the existing H01–H08 contact requirements, the latest saved
comparison figures, and the current twenty-job location table. It separates
case/unit H06, inside/outside H05, and panel/lid H07 applications. No contact face,
robot motion, tool model, grip force or acceptance threshold is newly selected.

The H04 working default remains T050, two linked fingers, 40 mm setback before
15-degree clockwise tilt. For the case, the later FC02 pin-passage comparison is
shown instead of reverting to FC01. The case fingers are not asserted to fit the
internal unit. The original requirements and observations are retained verbatim
under `sources/`; new records distinguish a historical comparison from adoption.

Existing draw functions are reused for dimensionless H01/H02/H03/H07/H08
schematics. Existing 3D figures are copied unchanged for H04, H05 and H06. Source
files are checked before and after copying; no native scene or motion is saved.

Prior-art check on 2026-09-23: `HVJB 支持引継ぎ 手先対応 工具空間`, exit 0,
one informational match and no blockers. The match was the 2026-09-15 UR15
feasibility survey. Its distinction between tool-envelope access and arm reach is
retained; no repeat of a reach or collision experiment is commissioned here.

This is a static, local review page and diagram set. Its purpose is to show which
contact concept belongs to which job and where the physical interface is still
unspecified. It does not certify stability or release the existing design gates.

The five legacy schematic functions were reused with their shape coordinates
unchanged. H02's two lower labels and H08's upper label were moved away from their
leader/arrow lines after visual inspection. The initial figures are retained in
`preview_schematics_01/`. The legacy source is stored as `.py.txt` so formatting
hooks do not alter the historical byte-preserved dependency.

The twelve application cards do not cover the target-specific H05 geometry for
D11, D21 and D61. Those gaps are explicit. P22 remains without a selected stage;
the historical D60/H08 family candidate is not a P22 process decision.
