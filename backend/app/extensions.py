from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# 循環インポートを防ぐため、拡張機能はここで初期化
db = SQLAlchemy()
socketio = SocketIO()

# 拡張機能の設定を簡単に行うための関数を追加
def init_extensions(app):
    """アプリケーションに拡張機能を初期化"""
    db.init_app(app)
    
    # SocketIOの設定
    socketio.init_app(
        app,
        async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'eventlet'),
        cors_allowed_origins=app.config.get('CORS_ALLOWED_ORIGINS', '*'),
        logger=app.debug,
        engineio_logger=app.debug
    )