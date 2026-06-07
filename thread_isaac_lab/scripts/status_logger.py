"""
シミュレーションステータスをJSONファイルに出力するユーティリティ
collect_goal_images.py から呼び出して使用
"""

import json
import time
import os
from datetime import datetime

STATUS_FILE = "/home/rlrk/data/realtime_status.json"
LOG_FILE = "/home/rlrk/data/status_history.jsonl"

# 定数
TABLE_HEIGHT = 0.75
MAX_REACH = 0.855  # Panda最大リーチ
MAX_VELOCITY = 2.0  # m/s
MAX_POSITION_ERROR = 0.1  # m
MAX_ORIENTATION_ERROR = 30  # degrees

class StatusLogger:
    def __init__(self):
        self.start_time = time.time()
        self.last_phase = None
        self.phase_start_time = time.time()
        self.consecutive_grasp_failures = 0
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    
    def log(self, data: dict):
        """ステータスをJSONファイルに出力"""
        
        # 基本情報
        status = {
            "timestamp": datetime.now().isoformat(),
            "elapsed": time.time() - self.start_time,
            "data": data,
            "alerts": [],
            "status": "OK"
        }
        
        # 異常検知
        alerts = self._detect_anomalies(data)
        status["alerts"] = alerts
        
        if any(a["level"] == "ERROR" for a in alerts):
            status["status"] = "ERROR"
        elif any(a["level"] == "WARNING" for a in alerts):
            status["status"] = "WARNING"
        
        # ファイル出力
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
        
        # 履歴追記
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(status) + "\n")
        
        return status
    
    def _detect_anomalies(self, data: dict) -> list:
        """異常検知"""
        alerts = []
        
        # === 幾何学的異常 ===
        
        # ハンドがテーブル下
        for arm in ["left", "right"]:
            ee_key = f"{arm}_ee_pos"
            if ee_key in data and data[ee_key] is not None:
                ee_z = data[ee_key][2] if len(data[ee_key]) > 2 else None
                if ee_z is not None and ee_z < TABLE_HEIGHT:
                    alerts.append({
                        "level": "ERROR",
                        "type": "GEOMETRY",
                        "message": f"{arm}ハンドがテーブル下 (Z={ee_z:.3f} < {TABLE_HEIGHT})"
                    })
        
        # 到達不能位置（ロボットベースからの距離）
        robot_base = data.get("robot_base_pos", [0, 0, 1.1])
        for arm in ["left", "right"]:
            target_key = f"{arm}_target_pos"
            if target_key in data and data[target_key] is not None:
                target = data[target_key]
                dist = ((target[0] - robot_base[0])**2 + 
                        (target[1] - robot_base[1])**2 + 
                        (target[2] - robot_base[2])**2) ** 0.5
                if dist > MAX_REACH:
                    alerts.append({
                        "level": "ERROR",
                        "type": "GEOMETRY",
                        "message": f"{arm}ターゲットが到達不能 (距離={dist:.3f}m > {MAX_REACH}m)"
                    })
        
        # === 物理的異常 ===
        
        # NaN検出
        for key, value in data.items():
            if isinstance(value, (list, tuple)):
                if any(v != v for v in value if isinstance(v, float)):  # NaN check
                    alerts.append({
                        "level": "ERROR",
                        "type": "PHYSICS",
                        "message": f"NaN検出: {key}"
                    })
            elif isinstance(value, float) and value != value:
                alerts.append({
                    "level": "ERROR",
                    "type": "PHYSICS",
                    "message": f"NaN検出: {key}"
                })
        
        # 異常速度
        for arm in ["left", "right"]:
            vel_key = f"{arm}_ee_vel"
            if vel_key in data and data[vel_key] is not None:
                vel = data[vel_key]
                speed = (vel[0]**2 + vel[1]**2 + vel[2]**2) ** 0.5
                if speed > MAX_VELOCITY:
                    alerts.append({
                        "level": "WARNING",
                        "type": "PHYSICS",
                        "message": f"{arm}異常速度 ({speed:.2f} m/s)"
                    })
        
        # === IK関連異常 ===
        
        # 位置誤差
        pos_error = data.get("position_error")
        if pos_error is not None and pos_error > MAX_POSITION_ERROR:
            alerts.append({
                "level": "ERROR" if pos_error > 0.3 else "WARNING",
                "type": "IK",
                "message": f"IK位置誤差大 ({pos_error:.3f}m)"
            })
        
        # 姿勢誤差
        ori_error = data.get("orientation_error_deg")
        if ori_error is not None and ori_error > MAX_ORIENTATION_ERROR:
            alerts.append({
                "level": "ERROR" if ori_error > 90 else "WARNING",
                "type": "IK",
                "message": f"IK姿勢誤差大 ({ori_error:.1f}°)"
            })
        
        # シンギュラリティ
        if data.get("singularity_detected"):
            alerts.append({
                "level": "ERROR",
                "type": "IK",
                "message": "IKシンギュラリティ検出"
            })
        
        # 関節限界
        joints_at_limit = data.get("joints_at_limit", [])
        if joints_at_limit:
            alerts.append({
                "level": "WARNING",
                "type": "IK",
                "message": f"関節限界: {joints_at_limit}"
            })
        
        # === タスク異常 ===
        
        # フェーズ停滞
        current_phase = data.get("phase")
        if current_phase != self.last_phase:
            self.last_phase = current_phase
            self.phase_start_time = time.time()
        elif current_phase is not None:
            phase_duration = time.time() - self.phase_start_time
            if phase_duration > 30:
                alerts.append({
                    "level": "WARNING",
                    "type": "TASK",
                    "message": f"フェーズ停滞 ({current_phase}, {phase_duration:.0f}秒)"
                })
        
        # 把持失敗
        if data.get("grasp_failed"):
            self.consecutive_grasp_failures += 1
            if self.consecutive_grasp_failures >= 3:
                alerts.append({
                    "level": "ERROR",
                    "type": "TASK",
                    "message": f"連続把持失敗 ({self.consecutive_grasp_failures}回)"
                })
        else:
            self.consecutive_grasp_failures = 0
        
        # === システム異常 ===
        
        # FPS
        fps = data.get("fps")
        if fps is not None and fps < 30:
            alerts.append({
                "level": "WARNING",
                "type": "SYSTEM",
                "message": f"FPS低下 ({fps:.1f})"
            })
        
        # GPU使用率
        gpu_memory_percent = data.get("gpu_memory_percent")
        if gpu_memory_percent is not None and gpu_memory_percent > 90:
            alerts.append({
                "level": "WARNING",
                "type": "SYSTEM",
                "message": f"GPU過負荷 ({gpu_memory_percent:.0f}%)"
            })
        
        return alerts


# シングルトンインスタンス
_logger = None

def get_logger():
    global _logger
    if _logger is None:
        _logger = StatusLogger()
    return _logger

def log_status(data: dict):
    return get_logger().log(data)
