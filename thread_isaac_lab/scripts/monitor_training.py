#!/usr/bin/env python3
"""訓練進捗の自動監視スクリプト"""
import subprocess
import time
import os
import re
from datetime import datetime, timedelta

def get_gpu_status():
    """GPU使用状況を取得"""
    result = subprocess.run(
        ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader'],
        capture_output=True, text=True
    )
    gpus = []
    for line in result.stdout.strip().split('\n'):
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 5:
            gpus.append({
                'index': parts[0],
                'name': parts[1],
                'memory_used': parts[2],
                'memory_total': parts[3],
                'utilization': parts[4]
            })
    return gpus

def get_training_processes():
    """訓練プロセスを取得"""
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True, text=True
    )
    processes = []
    for line in result.stdout.split('\n'):
        if 'python' in line and ('train' in line or 'collect' in line):
            if 'grep' not in line:
                parts = line.split()
                if len(parts) >= 11:
                    processes.append({
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3],
                        'cmd': ' '.join(parts[10:])[:60]
                    })
    return processes

def get_phase1_progress(log_path='/tmp/claude/tasks/phase1_training.log'):
    """Phase 1訓練の進捗を取得"""
    if not os.path.exists(log_path):
        return None
    
    try:
        with open(log_path, 'r') as f:
            content = f.read()
        
        # 最新のエポックとバッチを取得
        epoch_matches = re.findall(r'Epoch (\d+)/(\d+)', content)
        batch_matches = re.findall(r'Batch (\d+)/(\d+)', content)
        loss_matches = re.findall(r'loss[:\s]+([0-9.]+)', content, re.IGNORECASE)
        
        result = {}
        if epoch_matches:
            last = epoch_matches[-1]
            result['epoch'] = int(last[0])
            result['total_epochs'] = int(last[1])
        if batch_matches:
            last = batch_matches[-1]
            result['batch'] = int(last[0])
            result['total_batches'] = int(last[1])
        if loss_matches:
            result['loss'] = float(loss_matches[-1])
        
        return result if result else None
    except:
        return None

def estimate_remaining_time(progress, start_time=None):
    """残り時間を推定"""
    if not progress or 'epoch' not in progress:
        return "不明"
    
    epoch = progress['epoch']
    total = progress['total_epochs']
    
    # 1エポック約17分と仮定
    remaining_epochs = total - epoch
    remaining_minutes = remaining_epochs * 17
    
    hours = remaining_minutes // 60
    minutes = remaining_minutes % 60
    
    return f"{hours}時間{minutes}分"

def print_status():
    """ステータスを表示"""
    os.system('clear')
    print("=" * 60)
    print(f"THREAD 訓練モニター - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # GPU状況
    print("\n【GPU状況】")
    print("-" * 60)
    gpus = get_gpu_status()
    for gpu in gpus:
        print(f"  GPU {gpu['index']}: {gpu['name']}")
        print(f"    メモリ: {gpu['memory_used']} / {gpu['memory_total']}")
        print(f"    使用率: {gpu['utilization']}")
    
    # 訓練プロセス
    print("\n【訓練プロセス】")
    print("-" * 60)
    processes = get_training_processes()
    if processes:
        for p in processes:
            print(f"  PID {p['pid']}: CPU {p['cpu']}%, MEM {p['mem']}%")
            print(f"    {p['cmd']}")
    else:
        print("  訓練プロセスなし")
    
    # Phase 1進捗
    print("\n【Phase 1 World Model訓練】")
    print("-" * 60)
    progress = get_phase1_progress()
    if progress:
        if 'epoch' in progress:
            pct = (progress['epoch'] / progress['total_epochs']) * 100
            bar = '█' * int(pct // 5) + '░' * (20 - int(pct // 5))
            print(f"  進捗: Epoch {progress['epoch']}/{progress['total_epochs']} ({pct:.1f}%)")
            print(f"  [{bar}]")
        if 'batch' in progress:
            print(f"  バッチ: {progress['batch']}/{progress['total_batches']}")
        if 'loss' in progress:
            print(f"  Loss: {progress['loss']:.6f}")
        print(f"  残り時間: {estimate_remaining_time(progress)}")
    else:
        print("  ログファイルが見つかりません")
    
    # 次のステップ
    print("\n【次のステップ】")
    print("-" * 60)
    print("  1. Phase 1完了 → Phase 2訓練開始")
    print("  2. Phase 2完了 → Base Policy訓練")
    print("  3. Base Policy → Skill Adapter訓練")
    print("  4. MSA統合訓練")
    
    print("\n" + "=" * 60)
    print("Ctrl+C で終了 | 10秒ごとに更新")

def main():
    """メインループ"""
    try:
        while True:
            print_status()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n監視を終了しました")

if __name__ == "__main__":
    main()
