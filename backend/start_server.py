#!/usr/bin/env python3
"""
開発用サーバー起動スクリプト
環境設定とサーバー起動を自動化
"""

import os
import subprocess
import sys
from pathlib import Path

def check_environment():
    """環境チェック"""
    print("🔍 環境チェック中...")
    
    # Pythonバージョンチェック
    if sys.version_info < (3, 8):
        print("❌ Python 3.8以上が必要です")
        return False
    
    # 必要なファイルの存在確認
    required_files = [
        'requirements.txt',
        'config.py',
        'run.py',
        'app/__init__.py'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 必要なファイルが見つかりません: {file}")
            return False
    
    print("✅ 環境チェック完了")
    return True

def install_dependencies():
    """依存パッケージのインストール"""
    print("📦 依存パッケージをインストール中...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ 依存パッケージのインストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存パッケージのインストールに失敗: {e}")
        return False

def setup_environment():
    """環境設定"""
    print("⚙️ 環境設定中...")
    
    # .envファイルが存在しない場合は作成
    if not Path('.env').exists():
        try:
            with open('.env.example', 'r', encoding='utf-8') as f:
                example_content = f.read()
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(example_content)
            
            print("📝 .envファイルを作成しました。必要に応じて編集してください。")
        except Exception as e:
            print(f"⚠️ .envファイルの作成に失敗: {e}")
    
    # データベースディレクトリの作成
    db_dir = Path('instance')
    db_dir.mkdir(exist_ok=True)
    
    print("✅ 環境設定完了")

def start_server():
    """サーバー起動"""
    print("🚀 サーバーを起動中...")
    
    try:
        # 開発サーバーを起動
        subprocess.check_call([
            sys.executable, 'run.py'
        ])
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました")
    except subprocess.CalledProcessError as e:
        print(f"❌ サーバー起動に失敗: {e}")
        return False
    
    return True

def main():
    """メイン関数"""
    print("🎴 Midnight Luxury Poker サーバーセットアップ")
    print("=" * 50)
    
    # カレントディレクトリをスクリプトの場所に変更
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 環境チェック
    if not check_environment():
        sys.exit(1)
    
    # 依存パッケージのインストール
    if not install_dependencies():
        sys.exit(1)
    
    # 環境設定
    setup_environment()
    
    print("\n" + "=" * 50)
    print("✅ セットアップ完了！サーバーを起動します")
    print("📍 アクセスURL: http://127.0.0.1:5000")
    print("🛑 停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    # サーバー起動
    start_server()

if __name__ == '__main__':
    main()