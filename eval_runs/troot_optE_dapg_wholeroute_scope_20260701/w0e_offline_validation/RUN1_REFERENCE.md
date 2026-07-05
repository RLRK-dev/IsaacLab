# RUN-1 byte-identity 基準 (pre-build 凍結、%12 2026-07-05 16:58)

- **基準 npz sha256 = `3f44125551868e278ff53e3ad454242e7ade17bd7a87237061f03d1d9cc3235d`** (n_frames 7707)
- 三経路一致で確定: ①`p3_grid/cell_x0_y0/route_demo_raw_meta.json` npz_sha256 ②`p3_grid/sha_epoch_close/route_demo_raw_meta.json` (14:33 cuda:0 再走 EXACT MATCH) ③%12 自前 `sha256sum` on-disk 再計算。
- RUN-1 受入 = fix 後 build の nominal (0,0) 走行の `route_demo_raw.npz` sha256 が上記と一致 (%12 が raw file から独立再計算、%11 引用値を鵜呑みにしない)。meta 側は `head_sha`/`git_diff_sha256` が build 差で変わるのは期待どおり — 比較対象は **npz のみ**。run.log は nominal path 上に新規 print が無いことも併せて確認 (gate 分岐は offset 非 0 のみ)。
