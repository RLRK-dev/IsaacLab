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
