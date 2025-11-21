import logging
from flask import request
from flask_socketio import join_room, leave_room, emit
from app.extensions import socketio, db
from .game import Game
from .models import User
from .exceptions import PokerException
from .ai import EasyStrategy, NormalStrategy, HardStrategy

logger = logging.getLogger(__name__)

# ゲームインスタンスを管理する辞書
active_games = {}

# プレイヤーのセッション情報を管理する辞書 (SID -> プレイヤー情報)
player_sessions = {}

def get_or_create_game(room_id):
    """ルームIDに対応するゲームインスタンスを取得または作成"""
    if room_id not in active_games:
        active_games[room_id] = Game(room_id=room_id)
        logger.info(f"Created new game for room: {room_id}")
    return active_games[room_id]

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")
    sid = request.sid
    
    # セッション情報からプレイヤーを特定して削除
    if sid in player_sessions:
        session_info = player_sessions[sid]
        player_id = session_info['player_id']
        room_id = session_info['room_id']
        
        if room_id in active_games:
            game = active_games[room_id]
            # ゲームからプレイヤーを削除
            player = next((p for p in game.players if p.id == player_id), None)
            if player:
                game.remove_player(player.id)
                socketio.emit('player_disconnected', 
                              {"player_id": player.id, "username": player.name}, 
                              room=room_id)
                
                # 残ったプレイヤーに最新状態を送信
                broadcast_game_state(room_id)
        
        # セッション削除
        del player_sessions[sid]

@socketio.on('join_game')
def handle_join_game(data):
    """プレイヤーがゲームに参加するイベント"""
    username = data.get('username')
    room_id = data.get('room_id', 'default_room')
    # クライアントから送られた isAI フラグを取得
    is_ai = data.get('isAI', False)
    sid = request.sid
    
    if not username:
        socketio.emit('error', {'message': 'Username is required.'}, room=sid)
        return

    try:
        game = get_or_create_game(room_id)
        
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, chips=10000)
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user created: {username}")
        else:
            logger.info(f"Existing user joined: {username}")

        # ゲームに参加（データベースのUser IDを渡す）
        game.add_player(username, user.chips, is_ai=is_ai, player_id=user.id)
        
        # 人間のプレイヤーの場合のみ、セッション（ソケット）を紐づける
        if not is_ai:
            player_sessions[sid] = {
                'player_id': user.id,
                'room_id': room_id,
                'username': username
            }
            join_room(room_id)
            logger.info(f"Human Player {username} session bound to {sid}")
        else:
            logger.info(f"AI Player {username} added by {sid}")
        
        # 参加完了通知
        socketio.emit('joined_game', {
            "player_id": user.id,
            "username": username,
            "room_id": room_id,
            "chips": user.chips
        }, room=sid)
        
        # 全員に状態更新
        broadcast_game_state(room_id)
        
        # 他のプレイヤーへ通知
        socketio.emit('player_connected', {
            "player_id": user.id,
            "username": username
        }, room=room_id)

    except Exception as e:
        logger.error(f"Error in join_game: {e}")
        db.session.rollback()
        socketio.emit('error', {'message': str(e)}, room=sid)

@socketio.on('start_game')
def handle_start_game(data=None):
    """ゲーム開始イベント"""
    sid = request.sid
    # セッションからルームIDを取得
    room_id = player_sessions.get(sid, {}).get('room_id', 'default_room')
    
    try:
        game = get_or_create_game(room_id)
        
        active_players = [p for p in game.players if not p.is_ai and p.status != 'OUT']
        if len(active_players) < 1:
            socketio.emit('error', {'message': 'At least 1 human player is required to start.'}, room=sid)
            return

        game.start_hand()
        
        socketio.emit('game_started', {"message": "Game has started!"}, room=room_id)
        broadcast_game_state(room_id)
        
        handle_ai_turn(room_id)

    except Exception as e:
        logger.error(f"Error starting game: {e}")
        socketio.emit('error', {'message': str(e)}, room=sid)

@socketio.on('player_action')
def handle_player_action(data):
    """プレイヤーアクション処理"""
    sid = request.sid
    session_info = player_sessions.get(sid)
    
    if not session_info:
        socketio.emit('error', {'message': 'Player session not found. Please rejoin.'}, room=sid)
        return

    room_id = session_info['room_id']
    player_id = session_info['player_id']
    action = data.get('action')
    amount = data.get('amount')
    
    try:
        game = get_or_create_game(room_id)
        
        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            socketio.emit('error', {'message': 'Player not found in game.'}, room=sid)
            return

        game.player_action(player.name, action, amount)
        
        user = User.query.get(player_id)
        if user:
            user.chips = player.stack
            db.session.commit()
        
        broadcast_game_state(room_id)
        
        handle_ai_turn(room_id)

    except Exception as e:
        logger.error(f"Error in player_action: {e}")
        db.session.rollback()
        socketio.emit('error', {'message': str(e)}, room=sid)

def handle_ai_turn(room_id):
    """AIのターン処理"""
    try:
        game = get_or_create_game(room_id)
        
        while True:
            if game.turn_pos == -1 or game.phase in ["SHOWDOWN", "GAME_OVER"]:
                break
                
            current_player = game.players[game.turn_pos]
            
            if not current_player.is_ai or current_player.status in ['FOLDED', 'ALL_IN', 'OUT']:
                break

            if "Easy" in current_player.name:
                strategy = EasyStrategy()
            elif "Hard" in current_player.name:
                strategy = HardStrategy()
            else:
                strategy = NormalStrategy()

            action_data = strategy.get_action(current_player, game)
            
            amount = action_data.get('amount') if action_data.get('amount') is not None else 0
            
            game.player_action(current_player.name, action_data['action'], amount)
            
            broadcast_game_state(room_id)
            socketio.sleep(1)
            
            if game.turn_pos == -1 or not game.players[game.turn_pos].is_ai:
                break

        # 修正: ショーダウンに到達したら、結果を通知してモーダルを表示させる
        if game.phase == "SHOWDOWN":
            socketio.sleep(2) # アニメーション用の待機
            if game.last_action_info and 'winners' in game.last_action_info:
                # game_over イベントを送信 (これでフロントエンドのモーダルが開く)
                socketio.emit('game_over', game.last_action_info, room=room_id)

    except Exception as e:
        logger.error(f"Error in AI turn handling: {e}")

def broadcast_game_state(room_id):
    """ゲーム状態のブロードキャスト"""
    try:
        game = get_or_create_game(room_id)
        
        # 現在接続中の全プレイヤー（SIDを持っている人間）のリストを作成
        connected_player_ids = {info['player_id']: sid for sid, info in player_sessions.items() if info['room_id'] == room_id}

        # 1. まず、接続している各プレイヤーに「その人専用の（手札が見える）状態」を送る
        for player in game.players:
            if player.id in connected_player_ids:
                target_sid = connected_player_ids[player.id]
                player_state = game.get_state(perspective_player_name=player.name)
                socketio.emit('game_state_update', player_state, room=target_sid)
        
        # ルーム全体への一斉送信は行わない（個別送信でカバー）
        
    except Exception as e:
        logger.error(f"Error broadcasting game state: {e}")