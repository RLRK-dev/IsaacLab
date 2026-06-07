"""
Claude APIによる教示データ収集
- カメラ画像をClaude APIに送信
- スキルを選択・実行
- タスク関連データのみ収集
"""
import numpy as np
import torch
import base64
import anthropic
import json
import h5py
import cv2
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import argparse

# Isaac Lab imports
from omni.isaac.lab.app import AppLauncher

# スキル実行
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.skill_executor import SkillExecutor


class ClaudeGuidedCollector:
    """Claude APIガイドによるデータ収集"""
    
    def __init__(
        self,
        env,
        output_dir: str = "data/claude_guided",
        model: str = "claude-sonnet-4-20250514",
        save_images: bool = True,
    ):
        self.env = env
        self.client = anthropic.Anthropic()
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.save_images = save_images
        
        # スキル実行器
        self.skill_executor = SkillExecutor()
        
        # スキル定義
        self.skills = {
            "reach_left": "左手をケーブル左端へ移動",
            "reach_right": "右手をケーブル右端へ移動",
            "grasp_left": "左手で把持",
            "grasp_right": "右手で把持",
            "lift": "ケーブルを持ち上げる",
            "transport": "フックへ移動",
            "drape": "フックに掛ける",
            "release_left": "左手を解放",
            "release_right": "右手を解放",
            "done": "タスク完了",
        }
        
        self.system_prompt = f"""あなたはバイマニュアル（双腕）ロボットの操作アシスタントです。

タスク: テーブル上のケーブル（オレンジ色）をY字フック（青色）のV字部分に掛ける

利用可能なスキル:
{json.dumps(self.skills, ensure_ascii=False, indent=2)}

タスクの手順:
1. reach_left: 左手をケーブル左端へ
2. grasp_left: 左手で把持
3. reach_right: 右手をケーブル右端へ
4. grasp_right: 右手で把持
5. lift: ケーブルを持ち上げる
6. transport: フックへ移動
7. drape: フックに掛ける
8. release_left/release_right: 解放
9. done: 完了

画像を見て、現在の状態から次に実行すべきスキルを1つ選択してください。

出力形式（JSONのみ、説明不要）:
{{"skill": "スキル名", "reasoning": "理由（10文字以内）"}}
"""
        
        # データバッファ
        self.episode_data = []
        self.all_data = []
        
    def encode_image(self, image: np.ndarray) -> str:
        """画像をBase64エンコード"""
        # BGRからRGBに変換（OpenCV形式の場合）
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.standard_b64encode(buffer).decode("utf-8")
    
    def get_skill_from_claude(
        self,
        image: np.ndarray,
        task_state: Dict,
        retry_count: int = 3,
    ) -> Dict:
        """Claude APIからスキルを取得"""
        
        image_data = self.encode_image(image)
        
        # 状態情報を追加
        context = f"""
現在の状態:
- ケーブル-フック距離: {task_state.get('cable_hook_dist', 0):.3f}m
- 左手-ケーブル距離: {task_state.get('left_ee_cable_dist', 0):.3f}m
- 右手-ケーブル距離: {task_state.get('right_ee_cable_dist', 0):.3f}m
- 左グリッパー: {'閉' if self.skill_executor.left_gripper_closed else '開'}
- 右グリッパー: {'閉' if self.skill_executor.right_gripper_closed else '開'}
"""
        
        for attempt in range(retry_count):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=100,
                    system=self.system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_data,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": f"次のスキルを選択:{context}"
                                }
                            ],
                        }
                    ],
                )
                
                response_text = response.content[0].text
                
                # JSONを抽出
                import re
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if "skill" in result:
                        return result
                
            except Exception as e:
                print(f"  API error (attempt {attempt+1}): {e}")
                time.sleep(1)
        
        # フォールバック
        return {"skill": "idle", "reasoning": "API error"}
    
    def get_target_position(self, skill_name: str, task_state: Dict) -> Optional[np.ndarray]:
        """スキルに応じた目標位置を取得"""
        
        cable_segments = task_state.get("cable_segment_pos", None)
        hook_pos = task_state.get("hook_pos", None)
        
        if skill_name in ["reach_left", "grasp_left"]:
            # ケーブル左端
            if cable_segments is not None:
                return cable_segments[0]  # 最初のセグメント
            return None
            
        elif skill_name in ["reach_right", "grasp_right"]:
            # ケーブル右端
            if cable_segments is not None:
                return cable_segments[-1]  # 最後のセグメント
            return None
            
        elif skill_name in ["transport", "drape"]:
            # フック位置
            if hook_pos is not None:
                # フックの少し上を目標に
                return hook_pos + np.array([0, 0, 0.05])
            return None
            
        else:
            return None
    
    def get_current_state(self) -> Dict:
        """環境から現在の状態を取得"""
        # 環境のメソッドに依存
        state = {}
        
        if hasattr(self.env, 'get_ee_positions'):
            left_ee, right_ee = self.env.get_ee_positions()
            state["left_ee_pos"] = left_ee
            state["right_ee_pos"] = right_ee
        
        if hasattr(self.env, 'get_task_state'):
            task_state = self.env.get_task_state()
            state.update(task_state)
        
        return state
    
    def collect_episode(self, episode_id: int, max_steps: int = 100) -> List[Dict]:
        """1エピソード収集"""
        
        print(f"\n=== Episode {episode_id} ===")
        
        # 環境リセット
        obs = self.env.reset()
        self.skill_executor.reset()
        
        episode_data = []
        
        for step in range(max_steps):
            # 画像取得
            if hasattr(self.env, 'get_camera_image'):
                image = self.env.get_camera_image()
            else:
                # ダミー画像
                image = np.zeros((256, 256, 3), dtype=np.uint8)
            
            # 状態取得
            current_state = self.get_current_state()
            task_state = current_state.copy()
            
            # 距離情報を計算（環境から取得できない場合）
            if "cable_hook_dist" not in task_state:
                task_state["cable_hook_dist"] = 0.5
                task_state["left_ee_cable_dist"] = 0.3
                task_state["right_ee_cable_dist"] = 0.3
            
            # Claude APIでスキル選択
            skill_info = self.get_skill_from_claude(image, task_state)
            skill_name = skill_info.get("skill", "idle")
            reasoning = skill_info.get("reasoning", "")
            
            print(f"  Step {step:2d}: {skill_name:15s} ({reasoning})")
            
            # 完了判定
            if skill_name == "done":
                print("  => Task completed!")
                break
            
            # 目標位置取得
            target_pos = self.get_target_position(skill_name, task_state)
            
            # スキル実行
            action, skill_done = self.skill_executor.execute(
                skill_name, target_pos, current_state
            )
            
            # データ保存
            data_point = {
                "image": image.copy() if self.save_images else None,
                "task_state": self._flatten_task_state(task_state),
                "action": action.copy(),
                "skill": skill_name,
                "proprio": self._get_proprio(current_state),
            }
            episode_data.append(data_point)
            
            # 環境ステップ
            if hasattr(self.env, 'step'):
                obs, reward, done, info = self.env.step(action)
                
                if done:
                    print("  => Environment done")
                    break
            
            # スキル完了を待つ
            if not skill_done:
                # 複数ステップのスキルは完了まで継続
                for sub_step in range(20):
                    action, skill_done = self.skill_executor.execute(
                        skill_name, target_pos, self.get_current_state()
                    )
                    if hasattr(self.env, 'step'):
                        obs, reward, done, info = self.env.step(action)
                    if skill_done:
                        break
        
        print(f"  Collected {len(episode_data)} steps")
        return episode_data
    
    def _flatten_task_state(self, task_state: Dict) -> np.ndarray:
        """task_stateを44Dベクトルに変換"""
        result = np.zeros(44)
        
        # cable_segment_pos (30D)
        if "cable_segment_pos" in task_state:
            segments = np.array(task_state["cable_segment_pos"]).flatten()
            result[0:min(30, len(segments))] = segments[:30]
        
        # hook_pos (3D)
        if "hook_pos" in task_state:
            result[30:33] = task_state["hook_pos"]
        
        # left_ee_pos (3D)
        if "left_ee_pos" in task_state:
            result[33:36] = task_state["left_ee_pos"]
        
        # right_ee_pos (3D)
        if "right_ee_pos" in task_state:
            result[36:39] = task_state["right_ee_pos"]
        
        # distances (5D)
        result[39] = task_state.get("cable_hook_dist", 0)
        result[40] = task_state.get("left_ee_cable_dist", 0)
        result[41] = task_state.get("right_ee_cable_dist", 0)
        result[42] = task_state.get("left_ee_hook_dist", 0)
        result[43] = task_state.get("right_ee_hook_dist", 0)
        
        return result
    
    def _get_proprio(self, state: Dict) -> np.ndarray:
        """固有受容感覚を取得 (34D)"""
        proprio = np.zeros(34)
        
        # left_joint_pos (7D)
        if "left_joint_pos" in state:
            proprio[0:7] = state["left_joint_pos"][:7]
        
        # left_joint_vel (7D)
        if "left_joint_vel" in state:
            proprio[7:14] = state["left_joint_vel"][:7]
        
        # left_gripper (3D: pos, vel, force)
        proprio[14:17] = [0.04 if not self.skill_executor.left_gripper_closed else 0.0, 0, 0]
        
        # right_joint_pos (7D)
        if "right_joint_pos" in state:
            proprio[17:24] = state["right_joint_pos"][:7]
        
        # right_joint_vel (7D)
        if "right_joint_vel" in state:
            proprio[24:31] = state["right_joint_vel"][:7]
        
        # right_gripper (3D)
        proprio[31:34] = [0.04 if not self.skill_executor.right_gripper_closed else 0.0, 0, 0]
        
        return proprio
    
    def save_batch(self, data: List[Dict], batch_id: int):
        """バッチをHDF5で保存"""
        if not data:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"claude_guided_batch{batch_id:04d}_{timestamp}.h5"
        
        with h5py.File(filepath, 'w') as f:
            # 画像（JPEG圧縮）
            if self.save_images and data[0]["image"] is not None:
                images_group = f.create_group("images")
                for i, d in enumerate(data):
                    _, buffer = cv2.imencode('.jpg', d["image"], [cv2.IMWRITE_JPEG_QUALITY, 85])
                    images_group.create_dataset(f"{i:06d}", data=np.frombuffer(buffer, dtype=np.uint8))
            
            # task_state (44D)
            task_states = np.stack([d["task_state"] for d in data])
            f.create_dataset("task_states", data=task_states.astype(np.float32))
            
            # proprio (34D)
            proprios = np.stack([d["proprio"] for d in data])
            f.create_dataset("proprios", data=proprios.astype(np.float32))
            
            # actions (18D)
            actions = np.stack([d["action"] for d in data])
            f.create_dataset("actions", data=actions.astype(np.float32))
            
            # skills
            skills = [d["skill"].encode('utf-8') for d in data]
            f.create_dataset("skills", data=skills)
        
        print(f"Saved: {filepath} ({len(data)} samples)")
    
    def collect(self, num_episodes: int = 100, batch_size: int = 10):
        """データ収集メイン"""
        
        print("=" * 60)
        print("Claude API Guided Data Collection")
        print("=" * 60)
        print(f"Episodes: {num_episodes}")
        print(f"Output: {self.output_dir}")
        print(f"Model: {self.model}")
        print("=" * 60)
        
        all_data = []
        batch_id = 0
        
        for ep in range(num_episodes):
            episode_data = self.collect_episode(ep + 1)
            all_data.extend(episode_data)
            
            # バッチ保存
            if (ep + 1) % batch_size == 0:
                self.save_batch(all_data, batch_id)
                all_data = []
                batch_id += 1
        
        # 残りを保存
        if all_data:
            self.save_batch(all_data, batch_id)
        
        print("\n" + "=" * 60)
        print("Collection Complete!")
        print("=" * 60)


class DummyEnv:
    """テスト用ダミー環境"""
    
    def __init__(self):
        self.step_count = 0
        self.cable_pos = np.array([
            [0.3 + i * 0.04, 0.0, 0.52] for i in range(10)
        ])
        self.hook_pos = np.array([0.5, 0.0, 0.55])
        self.left_ee_pos = np.array([0.2, -0.2, 0.6])
        self.right_ee_pos = np.array([0.2, 0.2, 0.6])
    
    def reset(self):
        self.step_count = 0
        return {}
    
    def step(self, action):
        self.step_count += 1
        
        # 簡易シミュレーション
        self.left_ee_pos += action[0:3] * 0.01
        self.right_ee_pos += action[9:12] * 0.01
        
        done = self.step_count >= 100
        return {}, 0, done, {}
    
    def get_camera_image(self):
        # ダミー画像（グレー背景にテキスト）
        img = np.ones((256, 256, 3), dtype=np.uint8) * 128
        cv2.putText(img, f"Step {self.step_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return img
    
    def get_task_state(self):
        cable_hook_dist = np.linalg.norm(self.cable_pos[5] - self.hook_pos)
        left_ee_cable_dist = np.linalg.norm(self.left_ee_pos - self.cable_pos[0])
        right_ee_cable_dist = np.linalg.norm(self.right_ee_pos - self.cable_pos[-1])
        
        return {
            "cable_segment_pos": self.cable_pos,
            "hook_pos": self.hook_pos,
            "left_ee_pos": self.left_ee_pos,
            "right_ee_pos": self.right_ee_pos,
            "cable_hook_dist": cable_hook_dist,
            "left_ee_cable_dist": left_ee_cable_dist,
            "right_ee_cable_dist": right_ee_cable_dist,
            "left_ee_hook_dist": np.linalg.norm(self.left_ee_pos - self.hook_pos),
            "right_ee_hook_dist": np.linalg.norm(self.right_ee_pos - self.hook_pos),
        }
    
    def get_ee_positions(self):
        return self.left_ee_pos, self.right_ee_pos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_episodes", type=int, default=10)
    parser.add_argument("--output_dir", type=str, default="data/claude_guided")
    parser.add_argument("--test_mode", action="store_true", help="Use dummy environment")
    args = parser.parse_args()
    
    if args.test_mode:
        print("Running in TEST MODE with dummy environment")
        env = DummyEnv()
    else:
        # Isaac Lab環境を使用
        print("Isaac Lab environment integration required")
        # TODO: 実際のIsaac Lab環境を初期化
        env = DummyEnv()  # 一時的にダミーを使用
    
    collector = ClaudeGuidedCollector(
        env=env,
        output_dir=args.output_dir,
    )
    
    collector.collect(num_episodes=args.num_episodes)


if __name__ == "__main__":
    main()
