from flask import jsonify, request, send_from_directory
from . import poker_bp
from .models import User
from app.extensions import db
from config import Config
import os

# 修正ポイント: '..' を3回繰り返して、backendフォルダの外（プロジェクトルート）まで戻ります
# app/poker/routes.py (現在地)
#  -> app/poker (dirname)
#  -> app (..)
#  -> backend (..)
#  -> pokerプロジェクトルート (..)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

# サーバー起動時に正しいパスが出力されるか確認してください
print(f"DEBUG: Project Root is: {PROJECT_ROOT}")
print(f"DEBUG: FRONTEND_DIR is set to: {FRONTEND_DIR}")

@poker_bp.route('/')
def index():
    """ルートURL ('/') にアクセスされたときにメインのHTMLファイルを返す"""
    print(f"DEBUG: Accessing root URL, serving index.html from {FRONTEND_DIR}")
    return send_from_directory(FRONTEND_DIR, 'index.html')

@poker_bp.route('/<path:filename>')
def serve_static(filename):
    """静的ファイル (CSS, JS) を提供する"""
    print(f"DEBUG: Requesting static file: {filename}")
    return send_from_directory(FRONTEND_DIR, filename)

@poker_bp.route('/api/user', methods=['POST'])
def create_user():
    """新しいユーザーを作成"""
    data = request.get_json()
    if not data or not data.get('username'):
        return jsonify({'error': 'Username is required'}), 400
    
    password = data.get('password', '')
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    try:
        user = User(username=data['username'], chips=Config.DEFAULT_CHIPS)
        if password:
            user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.username} created successfully',
            'user_id': user.id,
            'chips': user.chips
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

@poker_bp.route('/api/user/<username>', methods=['GET'])
def get_user(username):
    """ユーザー情報を取得"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'username': user.username,
        'chips': user.chips,
        'user_id': user.id
    })

@poker_bp.route('/api/reset_user', methods=['POST'])
def reset_user_chips():
    """ユーザーチップリセット"""
    data = request.get_json()
    if not data or not data.get('username'):
        return jsonify({'error': 'Username is required'}), 400
    
    try:
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        user.chips = Config.DEFAULT_CHIPS
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.username} chips reset to {Config.DEFAULT_CHIPS}',
            'new_chips': user.chips
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

@poker_bp.route('/api/games', methods=['GET'])
def get_active_games():
    """アクティブなゲーム一覧を取得"""
    from .events import active_games
    
    games_info = []
    for room_id, game in active_games.items():
        games_info.append({
            'room_id': room_id,
            'phase': game.phase,
            'player_count': len(game.players),
            'active_players': len([p for p in game.players if p.status != 'OUT'])
        })
    
    return jsonify({'games': games_info})

@poker_bp.route('/api/game/<room_id>', methods=['GET'])
def get_game_state(room_id):
    """特定のゲームの状態を取得"""
    from .events import active_games
    
    if room_id not in active_games:
        return jsonify({'error': 'Game not found'}), 404
        
    game = active_games[room_id]
    return jsonify(game.get_state())