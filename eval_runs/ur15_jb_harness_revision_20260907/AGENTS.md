# UR15 production-line video work

Apply the repository AGENTS.md and THREAD Vault protocol.

## User-selected video format (2026-09-11)

- For all new revisions, render only the process view (`--views process`).
- Generate only `*_split_process_*_review.mp4`, with the process descriptions burned in.
- Use `scripts/encode_process_review_video.py` to encode the PNG frames directly into that MP4. Do not generate an intermediate raw MP4 or a separate wide-view movie.
- Put only this video type in new Downloads deliveries and ZIP archives. Native models, source, still images and verification records can accompany it.
- `data/video_delivery_policy.json` records the same user preference. Older encoders, orchestration scripts and four-video packages are historical reproduction inputs, not defaults for new work.

The user confirmed `UR15_JB_OP030_split_process_v06_review.mp4` and instructed proceeding to OP040 on 2026-09-11. Use the delivered v06 native and its recorded product state as the starting point. User review of the video is not a formal physical-validity verdict.

OP040's final-frame incoming snapshot is in `audit/op040_incoming_product_v01.json`. `OP040_工程・部品確認書_v01.md` proposes six new wires, an incoming distribution subassembly, and separate routing/fastening stations. These are review proposals, not accepted product requirements; do not treat the proposed D04 or extra station as present in v06.

On 2026-09-12 the user selected actual-product connection drawings and parts
lists, and requested searching the internet because no such files were available.
`analysis/op040_real_reference_research_20260912.md` records the public evidence
and its missing details. The Ampere product is a reference candidate, not an
adopted replacement for the v06 product. Keep unpublished dimensions and part
numbers unknown until their basis and the scope of the product change are set.

## User decisions received on 2026-09-13

- The user subsequently approved matching the Ampere public circuit and major
  components, including a new upstream product revision. Preserve v06. The
  September 12 candidate status above is historical; unpublished manufacturing
  dimensions and complete part numbers are still unknown.
- Divide work among three stations operating on separate workpieces in parallel.
  This does not require three arms at each station.
- Video/model motion production was paused. The currently authorized work is
  selecting hands and documenting their process roles before arm trajectories.
- Prefer a single arm where it completes the task. Retain OP030-A/B as the user's
  dual-arm candidates. Consider three arms only where their distinct roles are
  necessary; permission to consider them is not a selected three-arm mechanism.
- Consider two-, three-, and four-finger hands. Set the finger count, arrangement,
  drive configuration, fingertip geometry and grasp interfaces before designing
  complete arm motion. The supplied G3/G4 documents are design inputs, not
  verified product capabilities or automatically adopted acceptance criteria.
- The v06 B wire animation prescribes the full centerline and derives hand
  targets from it. Its length and geometry checks do not demonstrate physical
  S-bending using endpoint grasps. Do not present them as such.
- See `analysis/hand_selection_inputs_20260913.md` for source comparison,
  candidate roles and unresolved hand-selection inputs. Do not reinstate deleted
  cable hold-down mechanisms as an automatic response to the S-bend question.

## Subsequent handoff decision on 2026-09-13

- The user withdrew the pallet upper-retainer proposal and requested fastening
  while the fingers continue holding the cable/terminal. The v01 retainer pack
  is historical comparison evidence, not a hardware selection.
- Compare continuous hand retention and fastening at the same work position.
  Do not describe release at B followed by transport and regrasp at C as solving
  the unsupported interval. Do not invent a transport-capable temporary torque.
- Two holding arms plus station-mounted fastening units are a comparison
  candidate; no extra robot or selected fastening hardware is authorized by
  that candidate label. Keep the existing simultaneous different-size fastening
  requirement visible. Three-station task redistribution remains unresolved.
- `data/hand_held_fastening_v01.json` and the corresponding analysis document
  record the new direction. Existing hand-function v01 and fixture v01 describe
  the earlier handoff proposals. Arm trajectory and video production stay paused.
- The subsequent user `ok` authorized the next comparison step.
  `analysis/three_station_connection_groups_v01.md` proposes A for mechanical
  mounting, B for main/precharge/discharge power connections, and C for auxiliary
  and control connections. This is not a selected factory process or arm count.
  Actual common fastener stacks and incoming one-piece harnesses may change the
  B/C boundary; electrical common nodes do not establish physical shared bolts.
- `data/hand_target_contacts_v02.json` updates target-family station labels and
  holding periods for that proposal. Use F01-F10 for the current correspondence;
  the v01 A/B-prefixed IDs and placement-at-B/fastening-at-C notes are historical.
  Busbars and fuse bodies are assigned to their connection stage as candidates;
  separately supplied support bodies may be mounted at A. Two fingers remain
  the baseline comparison. Contact dimensions, force and installed hand counts
  are unselected, including the three targets without photo-location annotations.
- `analysis/hand_tool_access_v01.md` observes the unchanged isolated EDGE/GUIDE
  meshes. The 50 mm illustrative tool band has a different result from the
  extended band: in the near pose, the tool axis intersects a gripper-body
  surface at 120.577 mm above the sample connection plane. Do not extrapolate
  the short-band radial difference to a complete socket or fastening unit.
  The observation does not select tool dimensions, redesign the hand, or
  establish physical validity. Preserve the source mesh and saved poses when
  reproducing it; production arm motion and video remain paused.
- The user then requested moving the black hardware away from the terminal to
  maximize tool space. `analysis/hand_body_setback_v01.md` compares 30/60 mm
  rearward body offsets against the original EDGE sample. The original hardware
  geometry and four joint states are retained; the blue carriers extend while
  the terminal-side contact contours retain their world positions. Offsets,
  beam sections and tool cylinders are comparison values, not selected hardware.
  Upper tool space and lower fingertip space are separate observations. Existing
  carrier/mount surface overlaps remain recorded; mounting details, stiffness
  and force capability are unresolved. No upper retainer or arm motion is added.
- `analysis/hand_mount_interface_v02.md` records the subsequent mounting detail.
  The retained 2016-dated mesh matches the 2018 manual's 14 x 31 mm face, two
  3.4 mm clearances at 16 mm pitch, and central 3 mm indexing hole. The later
  2019 TM M5-center drawing does not match it. Keep that version distinction.
  The new 4 mm plate and nominal smooth M3/index bores are comparison geometry;
  no material, manufacturing fit, screw engagement or force criterion is chosen.
  The source hardware, contacts and saved transforms stay unchanged. Closed
  edge topology is observed, but zero-area tessellation faces and mounting
  surface contacts remain explicitly recorded; this is not manufacturing CAD
  or a physical acceptance verdict. Arm motion and video remain paused.

## Initial setback and root clamp decision on 2026-09-13

- The user selected 40 mm as the initial body setback and requested cable
  clamping at the mounting area as well as the existing terminal-side contact.
  The earlier 30/60 mm alternatives remain historical comparisons.
- `data/hand_root_clamp_v03.json` and `analysis/hand_root_clamp_v03.md` describe
  the new D40 sample: front terminal contours retained, paired root jacket
  pads at Y=61-71 mm, attached to the same original distal links. No separate
  actuator or upper retainer is added. The 10 mm contact length, reference
  14 mm wire and pad dimensions are comparison geometry, not identified Ampere
  parts or manufacturing specifications.
- Nominal pad surfaces match the saved wire facets. This does not establish
  pressure distribution or stable holding at both contact locations with one
  actuator. Pad material, compliance, attachment and screw access remain open;
  preserve the existing front contour's 0.1 mm display gap in observations.
- Four static poses, native readback, browser checks and surface-pair records
  are auxiliary observations. Original mounting contacts and degenerate faces
  remain recorded. Finger selection precedes arm motion and video production.

## Pad conditions comparison on 2026-09-14

- The user authorized the next pad-compliance/holding-condition study after
  confirming D40. `analysis/hand_pad_conditions_v01.md` compares P1 (terminal
  positioning contour and compliant root pad) before P2 (a guided passive root
  mechanism if pad compression is insufficient). Neither is manufacturing
  approval, and P2 has not been fitted into the current 3 mm backing space.
- The UI's closure, contact lead and stiffness ratio are a one-dimensional
  teaching example. Its normalized reactions are not N, four contact-force
  targets, friction capacities or gripper force commands. Actual values and
  acceptance requirements remain null in `data/hand_pad_conditions_v01.json`.
- Robotiq's public 60A silicone and the supplied G3/G4 draft's A30-50/3 mm are
  references, not selected D40 pad properties. Use measured compression,
  friction, pressure, time response and actual part limits before selecting
  force settings. Do not infer local pad forces from motor current or wrist
  resultant alone. Check the source-generation grasp-mode/equilibrium-line
  behavior; four saved poses do not establish its loaded behavior.

## Pad service comparison on 2026-09-14

- The subsequent user `ok` continued hand selection. The D40 service comparison
  in `analysis/hand_pad_service_v01.md` uses unchanged geometry and proposes
  replacing one complete custom fingertip through the original two screws.
  It does not select a separate root cartridge, adhesive, material or force.
- The retained holder takes its screws from the outer side (2018 manual p25).
  The root pads are absent from the measured outer 50 mm axial band in all four
  saved poses. Do not require removing them first solely because they overlap
  the inner-side screw projection. The 2 mm hex envelope and 50 mm shaft band
  do not establish access for a complete selected tool or screw extraction.
- Detached service translations sampled every 0.5 mm retain carrier/holder
  surface crossings in 10 of 25 samples per side. The local observation places
  the nonzero-offset crossing candidates near the mounting upper edge. Do not
  treat the last 12 mm illustration or zero later samples as a collision-free
  continuous removal path. Screw heads and the indexing pin are absent.
- During these observations, translate derived vertices instead of reassigning
  Blender scene matrices: the first attempt failed exact restoration because
  reassigning a matrix changes its floating-point decomposition. Keep the
  original mesh data and four poses intact, and retain the failed-run log.
- Root pad-to-support joining, support integration, mounting-edge relief,
  custom screw engagement and the needed pin travel remain design inputs.
  Physical acceptance, arm trajectories and video production remain outside
  this isolated service study.

## Mounting upper-edge comparison on 2026-09-14

- The following user `ok` authorized the local relief comparison recorded in
  `analysis/hand_mount_relief_v01.md`. Only four upper plate corners per side
  move, by 0.25 or 0.5 mm along the source mounting face. D40's original
  hardware, hole rims, terminal/root contacts and four poses stay unchanged.
  Neither relief value is selected for manufacture or an acceptance threshold.
- Repeating the same service samples gives surface pairs in nine of 24 positive
  offsets per side for the baseline and zero for both relief candidates. The
  zero-offset mounting surface pairs remain included in the full record.
  Do not infer continuous extraction, pin/screw access or loaded clearance from
  these samples. Original degenerate tessellation faces remain unmodified.
- Service sampling continues using derived world vertices without reassigning
  scene matrices. When comparing historical static reports, normalize only the
  candidate prefix in scene-qualified object names; keep measurements intact.
  Root support joining, material/compliance, screw engagement and actual
  manufacturing tolerances remain unresolved. Arm/video production stays paused.
