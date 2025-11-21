#!/usr/bin/env python3
"""
Midnight Luxury Poker - バックエンドエントリポイント
Flask + SocketIO によるリアルタイムポーカーゲームサーバー
"""

import os
import sys
import logging
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# アプリケーションのルートパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio

def setup_logging():
    """ロギング設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('poker_server.log', encoding='utf-8')
        ]
    )

def main():
    """メインエントリポイント"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 環境変数から設定を読み込み
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    # アプリケーションインスタンスを作成
    app = create_app()
    
    logger.info("🎴 Midnight Luxury Poker Server Starting...")
    logger.info(f"📍 Environment: {'DEVELOPMENT' if debug else 'PRODUCTION'}")
    logger.info(f"🌐 Server: http://{host}:{port}")
    logger.info(f"🔧 Debug Mode: {debug}")
    
    try:
        # SocketIOサーバーを起動
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            log_output=True,
            allow_unsafe_werkzeug=debug
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()