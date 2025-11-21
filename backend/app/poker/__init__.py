from flask import Blueprint

# ブループリントの作成
poker_bp = Blueprint('poker', __name__)

# 循環インポートを防ぐため、インポートは下部で
from . import routes, events

# ブループリントの登録後にSocketIOイベントを登録する関数
def register_socketio_events():
    """SocketIOイベントを登録"""
    from . import events
    # イベントは自動的に登録されるため、明示的な登録は不要