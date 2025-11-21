import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        # 開発環境用のデフォルトキーを提供
        SECRET_KEY = "dev-secret-key-change-in-production"
        print("⚠️  Warning: Using default SECRET_KEY. Set SECRET_KEY in .env for production.")

    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ('true', '1', 't')
    
    # データベース設定の修正
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///poker.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # カスタム設定の追加
    DEFAULT_CHIPS = 10000
    MAX_PLAYERS_PER_GAME = 6
    SOCKETIO_ASYNC_MODE = "eventlet"
    
    # CORS設定（本番環境では制限を厳しくする）
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")

config = Config()