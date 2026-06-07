"""
THREAD 学習時の自己改善システム
- 学習停滞検出 → API分析 → 報酬/パラメータ改善提案
"""
import numpy as np
import base64
import json
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

class TrainingMode(Enum):
    NORMAL = "normal"
    DEBUG = "debug"
    WAITING_FIX = "waiting_fix"

@dataclass
class StallDetectorConfig:
    window_size: int = 20
    min_improvement: float = 0.01
    patience: int = 3
    check_interval: int = 5

@dataclass
class TrainingMetrics:
    epoch: int
    loss: float
    reward_mean: float
    reward_std: float
    success_rate: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class TrainingDebugger:
    def __init__(self, project_root: str = None, config: StallDetectorConfig = None, enable_api: bool = True):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        self.project_root = Path(project_root).expanduser().resolve()
        self.config = config or StallDetectorConfig()
        self.enable_api = enable_api and HAS_ANTHROPIC
        
        self.debug_dir = self.project_root / "training_debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.report_path = self.project_root / "DEBUG_REPORT.md"
        
        if self.enable_api:
            try:
                self.client = anthropic.Anthropic()
            except:
                self.enable_api = False
        
        self.mode = TrainingMode.NORMAL
        self.metrics_history: List[TrainingMetrics] = []
        self.stall_count = 0
        self.api_call_count = 0
        self.improvement_history = []
        self.current_config = {"reward_weights": {}, "hyperparameters": {}, "network_config": {}}
        
        print(f"TrainingDebugger initialized (API: {self.enable_api})")

    def set_current_config(self, reward_weights: Dict = None, hyperparameters: Dict = None, network_config: Dict = None):
        if reward_weights: self.current_config["reward_weights"] = reward_weights
        if hyperparameters: self.current_config["hyperparameters"] = hyperparameters
        if network_config: self.current_config["network_config"] = network_config

    def log_metrics(self, epoch: int, loss: float, reward_mean: float, reward_std: float = 0, success_rate: float = 0) -> TrainingMode:
        self.metrics_history.append(TrainingMetrics(epoch=epoch, loss=loss, reward_mean=reward_mean, reward_std=reward_std, success_rate=success_rate))
        if epoch > 0 and epoch % self.config.check_interval == 0:
            self._check_stall()
        return self.mode

    def _check_stall(self) -> bool:
        if len(self.metrics_history) < self.config.window_size:
            return False
        recent = self.metrics_history[-self.config.window_size:]
        rewards = [m.reward_mean for m in recent]
        first_half, second_half = np.mean(rewards[:len(rewards)//2]), np.mean(rewards[len(rewards)//2:])
        improvement = 0 if first_half == 0 else (second_half - first_half) / abs(first_half)
        self.improvement_history.append(improvement)
        
        if improvement < self.config.min_improvement:
            self.stall_count += 1
            print(f"⚠️  停滞検出 ({self.stall_count}/{self.config.patience}): 改善率 {improvement:.2%}")
            if self.stall_count >= self.config.patience:
                self._enter_debug_mode()
                return True
        else:
            self.stall_count = 0
            print(f"✓ 学習進行中: 改善率 {improvement:.2%}")
        return False

    def _enter_debug_mode(self):
        self.mode = TrainingMode.DEBUG
        print("\n" + "="*60 + "\n🔍 学習停滞検出 - デバッグモード\n" + "="*60)
        curve_path = self._generate_learning_curve()
        analysis = self._analyze_with_api(curve_path) if self.enable_api else None
        self._generate_report(analysis, curve_path)
        self.mode = TrainingMode.WAITING_FIX
        self.stall_count = 0
        print(f"\n📝 レポート: {self.report_path}\n" + "="*60)

    def _generate_learning_curve(self) -> Path:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        epochs = [m.epoch for m in self.metrics_history]
        rewards = [m.reward_mean for m in self.metrics_history]
        losses = [m.loss for m in self.metrics_history]
        
        axes[0,0].plot(epochs, rewards, 'b-', lw=2); axes[0,0].set_title('Mean Reward'); axes[0,0].grid(True, alpha=0.3)
        axes[0,1].plot(epochs, losses, 'r-', lw=2); axes[0,1].set_title('Loss'); axes[0,1].grid(True, alpha=0.3)
        axes[1,0].plot(epochs, [m.success_rate for m in self.metrics_history], 'g-', lw=2); axes[1,0].set_title('Success Rate'); axes[1,0].grid(True, alpha=0.3)
        if self.improvement_history:
            colors = ['green' if i >= self.config.min_improvement else 'red' for i in self.improvement_history]
            axes[1,1].bar(range(len(self.improvement_history)), self.improvement_history, color=colors)
            axes[1,1].axhline(y=self.config.min_improvement, color='orange', ls='--')
        axes[1,1].set_title('Improvement Rate'); axes[1,1].grid(True, alpha=0.3)
        plt.tight_layout()
        
        curve_path = self.debug_dir / f"learning_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(curve_path, dpi=150); plt.close()
        return curve_path

    def _analyze_with_api(self, curve_path: Path) -> Dict:
        if not self.enable_api: return {"error": "API disabled"}
        with open(curve_path, "rb") as f:
            curve_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        
        prompt = f"""強化学習が停滞。分析して改善案をJSON形式で提案:
設定: {json.dumps(self.current_config, indent=2)}
メトリクス: rewards={[m.reward_mean for m in self.metrics_history[-10:]]}, improvement={self.improvement_history[-5:]}

出力形式:
{{"diagnosis": {{"cause": "原因", "reward_issues": ["問題"]}}, "fixes": {{"reward_weights": {{}}, "hyperparameters": {{}}}}, "priority": "high/medium/low"}}"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=2000,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": curve_b64}},
                    {"type": "text", "text": prompt}
                ]}]
            )
            self.api_call_count += 1
            import re
            match = re.search(r'\{.*\}', response.content[0].text, re.DOTALL)
            return json.loads(match.group()) if match else {"raw": response.content[0].text}
        except Exception as e:
            return {"error": str(e)}

    def _generate_report(self, analysis: Optional[Dict], curve_path: Path):
        latest = self.metrics_history[-1] if self.metrics_history else None
        report = f"""# 🔍 THREAD デバッグレポート

**生成**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**ステータス**: 🔴 修正待ち  
**学習曲線**: `{curve_path}`

## 現在の状態
- Epoch: {latest.epoch if latest else 'N/A'}
- Reward: {latest.reward_mean:.4f if latest else 'N/A'}
- 改善率: {self.improvement_history[-1]:.2%}

## 設定
```python
{json.dumps(self.current_config, indent=2)}
```

## API分析
"""
        if analysis:
            if "error" in analysis: report += f"Error: {analysis['error']}\n"
            elif "raw" in analysis: report += f"```\n{analysis['raw']}\n```\n"
            else: report += f"```json\n{json.dumps(analysis, indent=2, ensure_ascii=False)}\n```\n"
        else:
            report += "API分析なし\n"
        
        report += f"\n## 指示\n1. 上記を確認\n2. 修正適用\n3. ステータスを「✅修正完了」に変更\n4. 学習再開\n\nAPI呼出: {self.api_call_count}回 (¥{self.api_call_count*1.8:.0f})"
        
        with open(self.report_path, "w") as f: f.write(report)

    def mark_fixed(self):
        self.mode = TrainingMode.NORMAL
        self.stall_count = 0
        print("✅ 修正完了")

    def get_stats(self) -> Dict:
        return {"mode": self.mode.value, "epochs": len(self.metrics_history), "api_calls": self.api_call_count}

    def save_checkpoint(self, path: str = None):
        path = path or self.debug_dir / "debugger_state.json"
        with open(path, "w") as f:
            json.dump({"mode": self.mode.value, "stall_count": self.stall_count, "api_call_count": self.api_call_count,
                       "improvement_history": self.improvement_history, "current_config": self.current_config,
                       "metrics_history": [{"epoch": m.epoch, "loss": m.loss, "reward_mean": m.reward_mean, 
                                           "reward_std": m.reward_std, "success_rate": m.success_rate} for m in self.metrics_history]}, f)

    def load_checkpoint(self, path: str = None):
        path = Path(path or self.debug_dir / "debugger_state.json")
        if not path.exists(): return
        with open(path) as f: state = json.load(f)
        self.mode = TrainingMode(state["mode"])
        self.stall_count = state["stall_count"]
        self.api_call_count = state["api_call_count"]
        self.improvement_history = state["improvement_history"]
        self.current_config = state["current_config"]
        self.metrics_history = [TrainingMetrics(**m) for m in state["metrics_history"]]

    def test_api_connection(self) -> bool:
        """API接続テスト"""
        if not self.enable_api:
            print("API not enabled")
            return False
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say OK"}],
            )
            print(f"API OK: {response.content[0].text}")
            return True
        except Exception as e:
            print(f"API Error: {e}")
            return False

    def analyze_simulation_images(
        self,
        images: Dict[str, np.ndarray],
        context: str = "",
        save_images: bool = True,
    ) -> Dict:
        """
        シミュレーション画像をClaude APIで分析

        Args:
            images: カメラ名とnumpy画像のdict {"front": img, "left": img, "right": img}
            context: 追加のコンテキスト情報
            save_images: 画像を保存するか

        Returns:
            分析結果のdict
        """
        if not self.enable_api:
            return {"error": "API not enabled"}

        # 画像を保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_dir = self.debug_dir / f"sim_images_{timestamp}"
        image_dir.mkdir(parents=True, exist_ok=True)

        # Base64エンコード
        image_contents = []
        for name, img in images.items():
            if save_images:
                cv2.imwrite(str(image_dir / f"{name}.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

            # numpy to base64
            _, buffer = cv2.imencode('.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            img_b64 = base64.standard_b64encode(buffer).decode("utf-8")
            image_contents.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
            })

        prompt = f"""
シミュレーション画像を分析してください。

## カメラ構成
- Front: 前方45°俯角
- Left: 左後方45°俯角
- Right: 右後方45°俯角

## 検出対象
- オレンジ色のケーブル（10セグメント）
- 青色のY字フック
- 両腕のグリッパー位置

## コンテキスト
{context}

## 分析項目
1. ケーブルの状態（形状、位置）
2. フックの位置と向き
3. グリッパーとケーブル/フックの関係
4. 問題点や異常

JSON形式で回答:
{{
    "cable": {{"状態": "...", "位置": "..."}},
    "hook": {{"状態": "...", "位置": "..."}},
    "grippers": {{"left": "...", "right": "..."}},
    "issues": ["問題1", "問題2"],
    "suggestions": ["提案1", "提案2"]
}}
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": image_contents + [{"type": "text", "text": prompt}],
                }],
            )
            self.api_call_count += 1

            text = response.content[0].text
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"raw": text}
        except Exception as e:
            return {"error": str(e)}
