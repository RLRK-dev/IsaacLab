# p5 → p11：全 7 skill の EE 到達閾値（3 項付き・関節 bar 変換用）

**Author:** SKILL-DETAIL-DESIGN (w2:p5)。**2026-07-21 21:4x JST。** 受け皿 = `ARM_CONTROL_CONTROLLER_DRIVEN_ROUTE_DESIGN_V1…:5.4`（bank `57a4424774`）へ ingest 用。
**規律:** 全て code/config 直読。各閾値に p11 要求の 3 項 =(1)測定点 (2)測定瞬間 (3)基準 + H-4/H-5 routing を付す。⚠`ee_pos_*`=手首フランジ≠指先は反映済（[[reference-ee-pos-is-the-wrist-flange-not-the-fingertip-2026-07-15]]）。

## ⭐ 先に結論（PD gain sizing の binding）
- **arm PD の binding = acquire-grasp の指先 2mm・保持(sustained K=5)・目標姿勢との差** ⇒ **静定後ゆえ重力たわみ τ_bias/ke が縛る = ke(剛性)を駆動**（待っても消えない）。hold/wait/carry も同 2mm-保持を継承。
- ほとんどの success 閾値は **sustained/settled で評価** ⇒ **kd(追従ラグ)でなく ke(静的たわみ)を主に縛る**。動作中の tracking ラグは transient で、閾値自体は保持状態に課される。
- ⛔**cable 量（insert 溝 3mm・aerial 落下・approach の cable 成分）は腕 Jacobian で変換しない**＝H-5。arm 量のみ H-4。

## 閾値表（skill × 閾値 × 値 × (1)点 × (2)瞬間 × (3)基準 × routing）

| skill | 閾値 | 値(出典) | (1) 測定点 | (2) 瞬間 | (3) 基準 | routing |
|---|---|---|---|---|---|---|
| **acquire-grasp** | pos | **2mm**(`task_config:362 T_DIST`) | ⭐**指先** clamp_pos=`ee_pos+quat_rot(ee_q,[0,0,+0.220])`(`newton_skill_env_base.py:899-905`・`EE_TO_FINGERTIP=0.220`) | **保持 sustained K=5**(0.4s・`K_CLAMP=5`)→静的たわみ | **目標 clamp 姿勢**との差(pos error) | **H-4 @指先** |
| acquire-grasp | ori | **10°=0.1745rad**(`:364 T_ALIGN`) | 指先姿勢(own ori) | 保持 K=5 | 目標 clamp 姿勢との角度差 | H-4 @指先 |
| acquire-grasp | (finger) | 12mm(`:365 T_FINGER`) | **指開度**(gripper) | 保持 | 目標開度 | ⚠**gripper servo・腕でない** |
| **approach** | pos | **12mm**(`:363 T_DIST_APPROACH`) | **指先** clamp_pos | 保持 K=5 | ⭐**cable target 分節**(物体・obs[8:11]) | ⚠**H-4(腕→指令目標) + H-5(cable 位置)に分離**・⛔全 12mm を腕 Jacobian で変換不可 |
| **insert** | 着座 pos | **3mm**(`:368 T_GROOVE`) | ⭐**cable 分節 body**(腕でない・`newton_grip_env.py:1403`) | 着座時(settled cable) | **溝中心** `GROOVE_CENTER_Z=0.809`(`:226`) | ⛔**H-5(cable)・腕 Jacobian 不可** |
| insert | 着座 ori | cos>0.85(≈32°・`:369 T_SEAT`) | cable 分節 quat(`:1404`) | 着座時 | `GROOVE_TARGET_QUAT` | H-5(cable) |
| insert | (腕自身の押込) | PUSH_Z=1.025(`:95`) | 指先 | 動作中→保持 | push 深さ目標 | H-4 @指先(閾値でなく到達目標) |
| **aerial-regrasp** | R 接近 pos | 12mm(approach と同・`T_DIST_APPROACH`) | 指先 R | 保持 K=5 | cable 分節 R | H-4 @指先 + H-5(cable) |
| aerial-regrasp | 落下不可 | min(cable z)>**0.82**(`TABLE_HEIGHT+0.02`・`RL-Routing-Design.md:1662`) | **cable body 最小 z**(腕でない) | 動作中 通期 | table 面 | ⛔**H-5(cable)** |
| **carry(transport)** | 経由到達 | 明示数値なし(scripted 補間・`SETTLE_STEPS=200` 保持) | 指先/EE waypoint | 補間終→静定 | 目標 waypoint 姿勢 | H-4。⚠**許容は下流 skill 継承**=pre-grasp waypoint は grasp の 2mm 予算内に landing 要 |
| **hold** | drift 不可 | grasp 許容(2mm 保持) | 指先 | **静定**→静的たわみ | 保持中の目標姿勢 | **H-4 @指先**・ke 主 |
| **wait** | drift 不可 | incoming hold 継承 | 指先(保持腕) | **静定** | incoming hold の目標姿勢 | H-4 @指先(= hold と同・§0#1 保持連続) |
| **set_finger** | 指位置 | 0.002/0.006/0.04(`:274-277`) | **指 joint**(gripper) | 補間→静定 | 目標指位置 | ⚠**gripper servo・H-4/H-5 とも N/A** |

## 注記
- **孤立の 2mm/10° は目標姿勢との差**（agrasp/hold/wait）＝腕が自分で詰める量ゆえ H-4 で joint bar 化可能。**cable との距離**（approach/insert/aerial）は cable 運動を含むゆえ H-5 併用（⛔腕 Jacobian 単独不可）。
- **瞬間の効き**（p11 フレーム）: 保持/静定閾値（agrasp/hold/wait/carry 終端）→**τ_bias/ke（重力たわみ・待っても消えない）**。動作中閾値（aerial 落下・insert 押込 transient）→追従ラグ（kd/ke）*ω。⇒ **binding は保持側 2mm ゆえ ke sizing が主**。
- set_finger は腕 EE 量ゼロ（EE 動作なし）ゆえ arm PD に無関与。gripper servo の指位置精度のみ。
- 値の段階引き締め注記: `T_SEAT` は 0.85→0.9→0.95 の初期値（`:369`）。sizing は最終目標側で見るなら要確認。

## 非主張
- 本書は**閾値の 3 項化データ**。H-4 Jacobian / H-5 伝達比の**変換自体は p11 court**（私は routing のみ指定）。
- PD gain 値・ζ/kd/ke は p11。7-skill control-resource draft は別件（p4 greenlight 待ち）。
