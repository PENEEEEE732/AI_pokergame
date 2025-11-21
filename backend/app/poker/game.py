import random
import threading
from itertools import combinations
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
import uuid

from .ai import AIStrategy, EasyStrategy, NormalStrategy, HardStrategy
from .exceptions import InvalidActionException, NotPlayerTurnException, GameLogicException

# --- 定数定義 ---
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
RANK_VALUES = {rank: i for i, rank in enumerate(RANKS, 2)}

class Card:
    """カード一枚を表すクラス。"""
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.rank_value = RANK_VALUES[rank]

    def __repr__(self):
        return f"{self.rank}{self.suit[0]}"

class Deck:
    """52枚のカードデッキを表すクラス。"""
    def __init__(self):
        self.cards = [Card(s, r) for s in SUITS for r in RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        return self.cards.pop()

class HandEvaluator:
    """手札の役を判定するクラス。"""
    def evaluate_7_cards(self, cards: List[Card]) -> Tuple[str, Tuple]:
        """7枚のカードから最強の5枚の役を判定します。"""
        best_hand_rank = (-1,)
        best_hand_name = "High Card"

        for combo in combinations(cards, 5):
            hand_name, hand_rank = self._evaluate_5_card_hand(list(combo))
            if hand_rank > best_hand_rank:
                best_hand_rank = hand_rank
                best_hand_name = hand_name
        return best_hand_name, best_hand_rank

    def _evaluate_5_card_hand(self, hand: List[Card]) -> Tuple[str, Tuple]:
        """5枚の手札の役を判定します。"""
        values = sorted([card.rank_value for card in hand], reverse=True)
        suits = [card.suit for card in hand]
        is_flush = len(set(suits)) == 1
        is_straight = (max(values) - min(values) == 4 and len(set(values)) == 5) or (
            set(values) == {14, 2, 3, 4, 5}) # A-5ストレート
        
        if is_straight and set(values) == {14, 2, 3, 4, 5}:
             values = [5, 4, 3, 2, 1] # A-5ストレートのランクを補正

        counts = Counter(values)
        rank_counts = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
        
        if is_straight and is_flush:
            return "Straight Flush", (8,) + tuple(values)
        if rank_counts[0][1] == 4:
            return "Four of a Kind", (7, rank_counts[0][0], rank_counts[1][0])
        if rank_counts[0][1] == 3 and rank_counts[1][1] == 2:
            return "Full House", (6, rank_counts[0][0], rank_counts[1][0])
        if is_flush:
            return "Flush", (5,) + tuple(values)
        if is_straight:
            return "Straight", (4,) + tuple(values)
        if rank_counts[0][1] == 3:
            kicker1 = rank_counts[1][0]
            kicker2 = rank_counts[2][0]
            return "Three of a Kind", (3, rank_counts[0][0], kicker1, kicker2)
        if rank_counts[0][1] == 2 and rank_counts[1][1] == 2:
            kicker = rank_counts[2][0]
            pairs = sorted([rank_counts[0][0], rank_counts[1][0]], reverse=True)
            return "Two Pair", (2, pairs[0], pairs[1], kicker)
        if rank_counts[0][1] == 2:
            kickers = sorted([r[0] for r in rank_counts[1:]], reverse=True)
            return "One Pair", (1, rank_counts[0][0]) + tuple(kickers)
        
        return "High Card", (0,) + tuple(values)

class Player:
    """ゲームに参加するプレイヤーを表すクラス。"""
    def __init__(self, name: str, stack: int, strategy: Optional[AIStrategy] = None, player_id: str = None):
        self.id = player_id if player_id else str(uuid.uuid4())
        self.name = name
        self.initial_stack = stack
        self.stack = stack
        self.hand: List[Card] = []
        self.bet_this_round = 0
        self.bet_this_hand = 0
        self.status = "ACTIVE"  # ACTIVE, FOLDED, ALL_IN
        self.is_ai = strategy is not None
        self.strategy = strategy
        self.final_hand_name = None

    def reset_for_new_hand(self):
        self.hand = []
        self.bet_this_round = 0
        self.bet_this_hand = 0
        self.final_hand_name = None
        self.status = "ACTIVE" if self.stack > 0 else "OUT"

    def to_dict(self, show_hand=False):
        return {
            'id': self.id,
            'name': self.name,
            'stack': self.stack,
            'bet_this_round': self.bet_this_round,
            'hand': [{"rank": c.rank, "suit": c.suit} for c in self.hand] if show_hand else [],
            'status': self.status,
        }

class Game:
    """
    ポーカーゲーム全体のロジックと状態を管理するクラス。
    """
    def __init__(self, room_id: str, small_blind: int = 50, big_blind: int = 100):
        self.room_id = room_id
        self.players: List[Player] = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pots: List[Dict[str, Any]] = []
        self.phase = "WAITING"
        self.small_blind_amount = small_blind
        self.big_blind_amount = big_blind
        self.dealer_pos = 0 
        self.turn_pos = -1
        self.last_raiser_pos = -1
        self.current_bet = 0
        self.min_raise = big_blind 
        self.evaluator = HandEvaluator()
        self.lock = threading.Lock()
        self.last_action_info = None

    def add_player(self, name: str, stack: int, is_ai: bool = False, player_id: str = None):
        with self.lock:
            if len(self.players) >= 9:
                raise GameLogicException("Table is full.")
            
            if any(p.name == name for p in self.players):
                raise GameLogicException(f"Player {name} already in game.")
            
            strategy = None
            if is_ai:
                if "Easy" in name: 
                    strategy = EasyStrategy()
                elif "Hard" in name: 
                    strategy = HardStrategy()
                else: 
                    strategy = NormalStrategy()
            
            player = Player(name, stack, strategy, player_id=player_id)
            player.is_ai = is_ai
            self.players.append(player)
            
            if len(self.players) == 1:
                self.dealer_pos = 0

    def remove_player(self, player_id: str):
        """プレイヤーをゲームから削除"""
        with self.lock:
            self.players = [p for p in self.players if p.id != player_id]
            if len(self.players) < 2 and self.phase != "WAITING":
                self.reset_game()

    def reset_game(self):
        """ゲームをリセット"""
        with self.lock:
            for player in self.players:
                player.reset_for_new_hand()
            self.deck = Deck()
            self.community_cards = []
            self.pots = []
            self.phase = "WAITING"
            self.dealer_pos = 0
            self.turn_pos = -1
            self.last_raiser_pos = -1
            self.current_bet = 0
            self.min_raise = self.big_blind_amount
            self.last_action_info = None

    def start_hand(self):
        with self.lock:
            # --- ここから修正 ---
            # 1. 人間プレイヤーのリバイ（救済）処理
            # 人間プレイヤーのスタックが0になったら、ゲームオーバーにせず補充する
            for p in self.players:
                if not p.is_ai and p.stack <= 0:
                    p.stack = 10000  # 10,000チップ補充
                    p.status = "ACTIVE"
                    # 必要なら「リバイしました」等のメッセージをログに出す

            # 2. AIサバイバル処理
            # スタックが尽きたAIは容赦なく除外する
            surviving_players = [p for p in self.players if p.stack > 0]
            self.players = surviving_players

            # 3. プレイヤー数チェック
            if len(self.players) < 2:
                # プレイヤーが1人以下になった場合
                self.phase = "WAITING"
                return
            # --- ここまで修正 ---
            
            self.deck = Deck()
            self.community_cards = []
            self.pots = [{"amount": 0, "eligible_players": []}]
            self.last_action_info = None

            for p in self.players:
                p.reset_for_new_hand()

            self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
            
            sb_pos = (self.dealer_pos + 1) % len(self.players)
            bb_pos = (self.dealer_pos + 2) % len(self.players)
            self._post_blind(sb_pos, self.small_blind_amount)
            self._post_blind(bb_pos, self.big_blind_amount)

            self.current_bet = self.big_blind_amount
            self.min_raise = self._calculate_min_raise(self.big_blind_amount)
            
            for _ in range(2):
                for p in self.players:
                    if p.status != "OUT":
                        p.hand.append(self.deck.deal())

            self.turn_pos = (bb_pos + 1) % len(self.players)
            self.last_raiser_pos = bb_pos
            self.phase = "PREFLOP"

    def _post_blind(self, pos, amount):
        player = self.players[pos]
        blind_amount = min(player.stack, amount)
        player.stack -= blind_amount
        player.bet_this_round = blind_amount
        player.bet_this_hand = blind_amount
        if player.stack == 0:
            player.status = "ALL_IN"
        self.pots[0]['amount'] += blind_amount

    def _calculate_min_raise(self, raise_amount: int) -> int:
        """正しいミンレイズ計算"""
        if self.current_bet == 0:
            return max(self.big_blind_amount, raise_amount)
        else:
            return self.current_bet + max(self.big_blind_amount, raise_amount - self.current_bet)

    def _validate_bet_size(self, player: Player, amount: int) -> bool:
        """ベットサイズの検証"""
        if amount >= player.stack + player.bet_this_round:
            return True
        return amount >= self.min_raise

    def player_action(self, player_name: str, action: str, amount: int = 0):
        with self.lock:
            player = self._get_player_by_name(player_name)
            if not player or self.players[self.turn_pos] != player:
                raise NotPlayerTurnException(f"It's not {player_name}'s turn.")
            
            if action == 'fold':
                player.status = 'FOLDED'
            elif action == 'check':
                if player.bet_this_round < self.current_bet:
                    raise InvalidActionException("Cannot check, must call or raise.")
            elif action == 'call':
                call_amount = self.current_bet - player.bet_this_round
                if call_amount <= 0:
                    raise InvalidActionException("Cannot call, can check instead.")
                self._handle_bet(player, call_amount)
            elif action == 'raise' or action == 'bet':
                if not self._validate_bet_size(player, amount):
                     raise InvalidActionException(f"Raise must be at least {self.min_raise} or be an all-in.")
                if amount < self.current_bet:
                    raise InvalidActionException("Raise amount is less than current bet.")
                
                bet_amount = amount - player.bet_this_round
                self._handle_bet(player, bet_amount)
                
                raise_diff = amount - self.current_bet
                self.current_bet = amount
                if raise_diff > 0:
                    self.min_raise = amount + raise_diff
                
                self.last_raiser_pos = self.turn_pos
            else:
                raise InvalidActionException(f"Unknown action: {action}")

            self.last_action_info = {"player_name": player_name, "action": action, "amount": amount}
            self._next_turn()

    def _handle_bet(self, player, bet_amount):
        if bet_amount >= player.stack:
            actual_bet = player.stack
            player.bet_this_round += actual_bet
            player.bet_this_hand += actual_bet
            player.stack = 0
            player.status = "ALL_IN"
            if player.bet_this_round > self.current_bet:
                raise_diff = player.bet_this_round - self.current_bet
                if raise_diff >= self.big_blind_amount:
                     self.min_raise = player.bet_this_round + raise_diff
                self.current_bet = player.bet_this_round
                self.last_raiser_pos = self.turn_pos
        else:
            player.stack -= bet_amount
            player.bet_this_round += bet_amount
            player.bet_this_hand += bet_amount

    def _next_turn(self):
        if self._is_betting_round_over():
            self._end_betting_round()
            return

        self.turn_pos = (self.turn_pos + 1) % len(self.players)
        while self.players[self.turn_pos].status in ['FOLDED', 'ALL_IN', 'OUT']:
            self.turn_pos = (self.turn_pos + 1) % len(self.players)
            if self.turn_pos == self.last_raiser_pos:
                self._end_betting_round()
                return
        
        # AIの自動アクションは events.py で制御するためここでは何もしない

    def _is_betting_round_over(self) -> bool:
        active_players = [p for p in self.players if p.status == 'ACTIVE']
        if not active_players:
            return True
        
        if self.turn_pos != self.last_raiser_pos:
            return False

        first_bet = active_players[0].bet_this_round
        return all(p.bet_this_round == first_bet for p in active_players)

    def _end_betting_round(self):
        self._collect_bets_and_create_pots()
        
        self.turn_pos = (self.dealer_pos + 1) % len(self.players)
        self.current_bet = 0
        self.min_raise = self.big_blind_amount
        for p in self.players:
            p.bet_this_round = 0

        if self.phase == 'PREFLOP':
            self.phase = 'FLOP'
            for _ in range(3): self.community_cards.append(self.deck.deal())
        elif self.phase == 'FLOP':
            self.phase = 'TURN'
            self.community_cards.append(self.deck.deal())
        elif self.phase == 'TURN':
            self.phase = 'RIVER'
            self.community_cards.append(self.deck.deal())
        elif self.phase == 'RIVER':
            self.phase = 'SHOWDOWN'
            self._handle_showdown()
            return
        
        active_players_count = sum(1 for p in self.players if p.status in ['ACTIVE', 'ALL_IN'])
        if active_players_count <= 1:
            self._handle_showdown()
        else:
            self._next_turn()

    def _collect_bets_and_create_pots(self):
        all_in_players = sorted([p for p in self.players if p.status == 'ALL_IN' and p.bet_this_hand > 0], key=lambda p: p.bet_this_hand)
        active_bettors = [p for p in self.players if p.bet_this_hand > 0 and p.status != 'FOLDED']
        
        last_bet_level = 0
        self.pots = []

        for all_in_player in all_in_players:
            pot_level = all_in_player.bet_this_hand
            if pot_level <= last_bet_level:
                continue

            pot_amount = 0
            eligible_players = []
            
            for p in active_bettors:
                contribution = min(p.bet_this_hand, pot_level) - last_bet_level
                if contribution > 0:
                    pot_amount += contribution
                    if p.name not in [ep.name for ep in eligible_players]:
                         eligible_players.append(p)
            
            if pot_amount > 0:
                self.pots.append({'amount': pot_amount, 'eligible_players': [p.name for p in eligible_players]})
            last_bet_level = pot_level
        
        final_pot_amount = 0
        final_eligible_players = []
        for p in active_bettors:
            contribution = p.bet_this_hand - last_bet_level
            if contribution > 0:
                final_pot_amount += contribution
                if p.name not in [ep.name for ep in final_eligible_players]:
                    final_eligible_players.append(p)
        
        if final_pot_amount > 0:
            self.pots.append({'amount': final_pot_amount, 'eligible_players': [p.name for p in final_eligible_players]})

    def _handle_showdown(self):
        self.phase = "SHOWDOWN"
        winners_by_pot = []
        
        for i, pot in enumerate(self.pots):
            eligible_players = [p for p in self.players if p.name in pot['eligible_players'] and p.status != 'FOLDED']
            if not eligible_players:
                continue
            if len(eligible_players) == 1:
                winners = eligible_players
            else:
                best_rank = (-1,)
                winners = []
                for p in eligible_players:
                    hand_name, hand_rank = self.evaluator.evaluate_7_cards(p.hand + self.community_cards)
                    p.final_hand_name = hand_name
                    if hand_rank > best_rank:
                        best_rank = hand_rank
                        winners = [p]
                    elif hand_rank == best_rank:
                        winners.append(p)
            
            win_amount_per_player = pot['amount'] // len(winners)
            for winner in winners:
                winner.stack += win_amount_per_player
                winners_by_pot.append({
                    "player": winner.name,
                    "pot_name": f"Pot {i+1}",
                    "amount": win_amount_per_player,
                    "hand": winner.final_hand_name
                })
        
        self.last_action_info = {"winners": winners_by_pot}

    def get_state(self, perspective_player_name: Optional[str] = None) -> Dict[str, Any]:
        with self.lock:
            player_states = []
            for i, p in enumerate(self.players):
                is_perspective = p.name == perspective_player_name
                
                # フェーズがSHOWDOWNの場合、フォールドしていない全プレイヤーの手札を公開する
                show_hand = is_perspective or (self.phase == 'SHOWDOWN' and p.status != 'FOLDED')
                
                p_state = p.to_dict(show_hand=show_hand)
                p_state['is_turn'] = (self.turn_pos != -1 and i == self.turn_pos)
                p_state['is_dealer'] = (i == self.dealer_pos)
                p_state['is_small_blind'] = (i == ((self.dealer_pos + 1) % len(self.players)))
                p_state['is_big_blind'] = (i == ((self.dealer_pos + 2) % len(self.players)))
                player_states.append(p_state)

            return {
                "room_id": self.room_id,
                "phase": self.phase,
                "community_cards": [{"rank": c.rank, "suit": c.suit} for c in self.community_cards],
                "pots": self.get_pots_info(),
                "players": player_states,
                "current_bet": self.current_bet,
                "min_raise": self.min_raise,
                "last_action": self.last_action_info
            }

    def get_pots_info(self) -> List[Dict[str, Any]]:
        if not self.pots:
            total_bets = sum(p.bet_this_hand for p in self.players)
            if total_bets > 0:
                return [{
                    "name": "Main Pot", 
                    "amount": total_bets,
                    "eligible_players": [p.name for p in self.players if p.status != 'FOLDED']
                }]
        return self.pots

    def get_possible_actions(self, player: Player) -> Dict[str, Any]:
        can_check = player.bet_this_round == self.current_bet
        can_call = not can_check and player.stack > 0
        call_amount = self.current_bet - player.bet_this_round
        can_raise = player.stack > call_amount
        return {
            "can_check": can_check,
            "can_call": can_call,
            "call_amount": call_amount,
            "can_raise": can_raise,
            "min_raise": self.min_raise,
            "all_in_amount": player.stack + player.bet_this_round
        }

    def _get_player_by_name(self, name: str) -> Optional[Player]:
        return next((p for p in self.players if p.name == name), None)