#!/usr/bin/env bash
# Regenerate SHA256SUMS.txt for the package (run from the package dir). Excludes SHA256SUMS.txt itself.
set -euo pipefail
cd "$(dirname "$0")"
sha256sum 00_*.md 01_*.md 02_*.csv 03_*.csv 04_*.md 05_*.md 06_*.md 07_*.md 08_*.md 09_*.json 10_*.md 11_*.md \
  check_review_candidate.py verify_exact_baseline_pins.sh regen_sha256sums.sh \
  review_records/*.md review_records/fold/* review_records/rs_consult/*.md review_records/rs_consult/A_GPTastra_20260906/* \
  review_records/baselines/SHA256SUMS.txt review_records/baselines/*/* review_records/trace/* > SHA256SUMS.txt
wc -l SHA256SUMS.txt
