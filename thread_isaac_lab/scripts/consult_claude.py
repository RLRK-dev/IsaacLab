#!/home/rlrk/IsaacLab/env_isaaclab/bin/python
"""Claude APIを使って設計・実装の改善提案を得る"""
import anthropic
import sys
import os

def consult(problem: str) -> str:
    client = anthropic.Anthropic()
    
    # CLAUDE.mdから設計仕様を読み込み
    claude_md_path = os.path.expanduser("~/IsaacLab/CLAUDE.md")
    try:
        with open(claude_md_path, "r") as f:
            design_spec = f.read()
    except FileNotFoundError:
        design_spec = "設計仕様ファイルが見つかりません"
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=f"""あなたはTHREADプロジェクト（双腕ロボットによるケーブル操作）の設計者です。
Isaac Lab 2.3.0、PyTorch 2.7、CUDA 12.8を使用しています。

以下が設計仕様です:

{design_spec}

問題を分析し、具体的で実装可能な改善提案を日本語で提供してください。""",
        messages=[{
            "role": "user",
            "content": f"以下の問題について改善提案してください:\n\n{problem}"
        }]
    )
    return response.content[0].text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    else:
        print("問題を入力してください (Ctrl+Dで終了):")
        problem = sys.stdin.read()
    
    print("\n" + "="*60)
    print("Claude APIからの改善提案")
    print("="*60 + "\n")
    print(consult(problem))
