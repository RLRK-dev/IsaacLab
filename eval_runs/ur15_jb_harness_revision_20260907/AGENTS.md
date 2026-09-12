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
