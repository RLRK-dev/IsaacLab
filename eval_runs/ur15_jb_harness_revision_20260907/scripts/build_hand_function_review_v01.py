# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build an offline hand-function comparison without loading robot scenes."""

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

REVISION = Path(__file__).resolve().parents[1]
CONFIG = "data/hand_function_selection_v01.json"
TEMPLATE = "scripts/hand_function_viewer_v01.html"
PAGE = "B工程_指構成と引渡し_v01.html"
DOCUMENT = "B工程_指構成整理_v01.md"


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of the given file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_observations(config: dict, terminal: dict) -> dict:
    """Record configuration arithmetic, without measuring holding capability."""
    edge = sum(terminal["insert"]["edge_y_range_m"]) / 2
    rear = sum(terminal["insert"]["rear_guide_y_range_m"]) / 2
    spacing = rear - edge
    g4 = config["hand_definitions"]["G4"]
    lower, upper = g4["alternative_mount_spacing_range_m"]
    allocations = []
    for hands in (("2F", "2F"), ("2F", "G4"), ("G4", "G4")):
        definitions = [config["hand_definitions"][hand] for hand in hands]
        allocations.append(
            {
                "hands": list(hands),
                "arms": 2,
                "fingers": sum(hand["fingers"] for hand in definitions),
                "closing_actuators": sum(hand["closing_actuators"] for hand in definitions),
            }
        )
    return {
        "basis": "read-only configuration arithmetic; not measured hardware or physical acceptance",
        "edge_interval_center_y_m": edge,
        "guide_interval_center_y_m": rear,
        "terminal_example_center_spacing_m": spacing,
        "g4_initial_spacing_m": g4["initial_pair_spacing_m"],
        "g4_comparison_mount_range_m": [lower, upper],
        "example_centers_within_initial_comparison_mount_range": lower <= spacing <= upper,
        "mount_range_is_verified_hardware_limit": False,
        "allocations": allocations,
        "physical_acceptance_verdict": None,
    }


def build_document(config: dict, facts: dict) -> str:
    """Describe the functional baseline and outstanding handoff definition."""
    rows = "\n".join(
        f"| {step['id']} {step['label_ja']} | {step['hand_function_ja']} | {step['note_ja']} |"
        for step in config["process_steps"]
    )
    allocations = "\n".join(
        f"| {'＋'.join(item['hands'])} | {item['arms']} | {item['fingers']} | {item['closing_actuators']} |"
        for item in facts["allocations"]
    )
    edge = facts["edge_interval_center_y_m"] * 1000
    rear = facts["guide_interval_center_y_m"] * 1000
    distance = facts["terminal_example_center_spacing_m"] * 1000
    roles = "\n".join(f"- **{station}**：{role}" for station, role in config["station_roles_preserved"].items())
    questions = "\n".join(f"- {item}" for item in config["handoff"]["drawing_gates_not_acceptance_limits_ja"])
    return f"""# B工程の指構成と、Cへの引渡し v0.1

2026-09-13。根拠はユーザーの工程要求、受領G3/G4仕様案、前回の静的指先設定、メーカー資料の読取り。
ハンドの役割を絞る資料であり、採用済み製作仕様・新しい受入基準ではない。

## 今回の絞り込み

**Bは「双腕・各2本指」を機能比較の基準にする。** {config["baseline"]["reason_ja"]}
端子側は側縁用の専用輪郭、被覆だけを持つ箇所では短い丸底溝を比較する。
前回のGUIDEは2本指に固定した被覆のすき間案内であり、端子とは別の力で被覆を締める部品ではない。
端子側だけのEDGEと、案内を加えるGUIDEの実物適合・必要性は未確定である。

端子保持中に被覆側だけ開く／被覆保持中に端子側だけ開く、といった役割が必要になった場合に、
**その役割を持つ手だけ**G4を比較する。G3は剛体部品の3点位置決めを目的とする候補に残す。
G3の1対2配置は、G4のような独立した対向保持組2組ではない。
どの構成についても把持力、滑り、端子の回転、被覆損傷、実際のS字形成は未検証である。

## 工程要求との対応

| 段階 | 手に必要な役割 | 選定への意味・残る点 |
| --- | --- | --- |
{rows}

左右それぞれの2Fは、別の手としてそれぞれ開閉指令を受ける。同時接近・同時クランプ・同時上昇は、
各手の中に3本／4本の独立指を設けることとは別の要求である。
経路形成と最終位置合わせで、どの局所支持・接触の切替が必要かはまだ確定していない。
その未確定を「2Fで全作業成立済み」と読み替えない。

## G4を比較する場合の具体差分

G4仕様案では各指をX方向へ個別に開閉でき、前後の対向組を別々に扱う。
ただし、片組を開くときに残る組だけで保持できるかは、全指保持とは別に確認する仕様である。
独立した開閉指令があることと、対象を実際に保持できることを分ける。
指の追加だけで通常の2F-85がこの機構になるわけではない。

| 両腕の構成候補 | 腕の本数 | 指の総数 | 開閉用アクチュエータ数 |
| --- | ---: | ---: | ---: |
{allocations}

数は既存2Fと受領G4案からの算術で、全ロボットの駆動数・費用・信頼性・優劣を表さない。
G4が必要な側は未指定であり、2F＋G4は左右を固定した割当ではない。

**前回の指先をG4へそのまま移す配置にはならない。** 端子の候補区間4〜12 mmの中心は{edge:g} mm、
後方案内48〜56 mmの中心は{rear:g} mmで、両中心の差は{distance:g} mm。
G4の初期30 mm、比較用の別取付20〜40 mmの範囲とは異なる。
44 mmは現在のサンプル用輪郭と案内の配置から計算した値で、Ampere実部品の必要間隔ではない。
20〜40 mmも実証済みの機械限界ではない。G4を選ぶ場合は対象と接触位置から再配置を検討する。

G4の保持組間隔は運転中固定である。各指のX開閉・受動傾きは、ケーブル長手方向Yへ送る駆動軸ではない。
後方組を開くことを「線を能動的に送り込める」と説明しない。
2本指・4本指のどちらも、両端の姿勢を指令するだけで所定S字が得られるとは確認されていない。
公開製品に必要な配線経路も旧H03のS字へ自動的に置き換えない。

## BからCへ渡すときの未確定事項

**Bの両手を開いた後、Cで締結するまで端子・配線を何が保持するかは未定。**
この期間は2F、G3、G4のいずれを選んでもハンドの保持が残らない。
図中で対象を同じ場所に表示しても、実際にその位置を維持できる証拠にはしない。

次に図面へ対応付ける内容は次のとおり。新しい数値の受入条件は設定していない。

{questions}

旧 `op030_split_wire_motion.py` にはスタッド／サドルを示す支持名と、任意クリップ分岐がある。
これはコードの記述を読んだ事実であり、現行v06の有効設定・実際の拘束・Ampere新版の保持を確認したものではない。
撤去済みの青い押さえを復活させたり、Bで仮締めを追加したりして未確定欄を埋めていない。

## A・Cへ引き継ぐ割当

{roles}

今回具体化したのは機能比較の基準と追加指の検討理由まで。
採用部品の接触面・指構成・開放方法と上記の引渡しを確定してから、手先カメラ・アーム軌道の検討へ進める。
正式な物理妥当性判定はVaultProtocol V12の独立レビュー経路による。

## 出典・再現

- [Robotiq General Presentation]({config["sources"]["robotiq_url"]})：単一アクチュエータによる両指の開閉。
  2026-09-13に参照。
- [受領G3/G4仕様案 v0.2]({config["sources"]["user_spec_path"]})：§3、§4.1–4.2、§7.1–7.2。設計案として使用。
- [前回の端末指先比較設定]({config["sources"]["terminal_config_path"]})：接触区間の算術。実物測定ではない。
- [前回の静的3D比較記録]({config["sources"]["terminal_review_path"]})：形状・出典・未確定事項。
  今回の配布には3Dモデルを再収録していない。
- [今回の機能対応データ]({CONFIG})と[算術・入力SHAの記録](audit/hand_function_observations_v01.json)。

再生成はリポジトリルートから `./isaaclab.sh -p <本スクリプトのパス> --output_dir <新規フォルダー>`。
本スクリプトは `eval_runs/ur15_jb_harness_revision_20260907/scripts/build_hand_function_review_v01.py`。
入力が同じなら同じ説明内容を生成する。HTMLは同梱データを内蔵し、ネット接続なしで操作できる。
アーム軌道、動画、既存native、v07の保留裁定はこの生成器で変更しない。
"""


def main() -> None:
    """Write a new, self-contained review directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to replace existing output: {output}")
    config = json.loads((REVISION / CONFIG).read_text())
    sources = config["sources"]
    observed_sha = file_sha256(REVISION / sources["user_spec_path"])
    if observed_sha != sources["user_spec_sha256"]:
        raise ValueError(f"User specification SHA mismatch: {observed_sha}")
    terminal = json.loads((REVISION / sources["terminal_config_path"]).read_text())
    facts = derive_observations(config, terminal)
    input_paths = [
        CONFIG,
        TEMPLATE,
        sources["user_spec_path"],
        sources["terminal_config_path"],
        sources["terminal_review_path"],
        sources["historical_motion_path"],
        "scripts/build_hand_function_review_v01.py",
    ]
    audit = {
        "observed_at": datetime.now().astimezone().isoformat(),
        "observations": facts,
        "input_sha256": {path: file_sha256(REVISION / path) for path in input_paths},
        "browser_observations": "recorded separately after generation",
        "scene_loaded": False,
        "physical_acceptance_verdict": None,
    }
    output.mkdir(parents=True)
    for path in input_paths:
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REVISION / path, destination)
    embedded = json.dumps({"config": config, "facts": facts}, ensure_ascii=False).replace("<", "\\u003c")
    template = (REVISION / TEMPLATE).read_text()
    if template.count("__REVIEW_DATA__") != 1:
        raise ValueError("Expected one data placeholder")
    (output / PAGE).write_text(template.replace("__REVIEW_DATA__", embedded))
    (output / DOCUMENT).write_text(build_document(config, facts))
    (output / "audit").mkdir()
    (output / "audit/hand_function_observations_v01.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(facts, indent=2, ensure_ascii=False))
    print(f"DONE: {output / PAGE}")


if __name__ == "__main__":
    main()
