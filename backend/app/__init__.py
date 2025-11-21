import logging
from flask import Flask, jsonify
from config import Config
from .extensions import db, socketio, init_extensions

def create_app(config_class=Config):
    """アプリケーションファクトリ - 最終版"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.info("🎴 Midnight Luxury Poker App Initializing...")

    # 拡張機能の初期化
    init_extensions(app)
    app.logger.info("✅ Extensions initialized")

    # ブループリントの登録
    from .poker import poker_bp
    app.register_blueprint(poker_bp)
    app.logger.info("✅ Blueprints registered")

    # データベースの初期化
    with app.app_context():
        db.create_all()
        app.logger.info("✅ Database initialized")

    # ヘルスチェックエンドポイントの追加
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'poker-game'})

    app.logger.info("🚀 Application setup completed successfully")
    return app