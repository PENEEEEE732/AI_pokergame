import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from .game import Game, Player
    from .game import Card

class AIStrategy(ABC):
    @abstractmethod
    def get_action(self, player: 'Player', game: 'Game') -> Dict[str, Any]:
        pass

    def _get_safe_call_action(self, possible_actions: Dict[str, Any]) -> Dict[str, Any]:
        """安全なコールアクションを返すヘルパーメソッド"""
        if possible_actions.get('can_check', False):
            return {'action': 'check'}
        if possible_actions.get('can_call', False):
            return {'action': 'call'}
        return {'action': 'fold'}

    def _get_safe_raise_action(self, player: 'Player', possible_actions: Dict[str, Any], target_amount: int) -> Dict[str, Any]:
        """安全なレイズアクションを返すヘルパーメソッド
        - 最低レイズ額を下回る場合は補正する
        - チップが足りない場合はオールインまたはコールに変更する
        """
        min_raise = possible_actions.get('min_raise', 0)
        max_bet = player.stack + player.bet_this_round # 自分の全財産（場に出した分含む）

        # レイズ額が最低額未満なら、最低額に合わせる
        if target_amount < min_raise:
            target_amount = min_raise

        # 全財産を超えている場合（チップ不足）
        if target_amount >= max_bet:
            # オールイン (レイズ扱いだが額は全財産)
            return {'action': 'raise', 'amount': max_bet}
        
        # 通常のレイズ
        return {'action': 'raise', 'amount': target_amount}

class EasyStrategy(AIStrategy):
    def get_action(self, player: 'Player', game: 'Game') -> Dict[str, Any]:
        try:
            possible_actions = game.get_possible_actions(player)
            if not any(possible_actions.values()): return {'action': 'fold'}
            
            if possible_actions.get('can_check', False):
                return {'action': 'check'}

            hand_strength = self._basic_hand_evaluation(player.hand)
            call_amount = possible_actions.get('call_amount', 0)
            stack_ratio = call_amount / (player.stack + 1)
            
            # リスク管理
            if stack_ratio > 0.2 and hand_strength < 0.4:
                return {'action': 'fold'}
            if stack_ratio > 0.5 and hand_strength < 0.7:
                return {'action': 'fold'}

            # アクション決定
            if hand_strength > 0.7 and possible_actions.get('can_raise', False) and random.random() < 0.2:
                min_raise = possible_actions.get('min_raise', 100)
                return self._get_safe_raise_action(player, possible_actions, min_raise)
            
            return self._get_safe_call_action(possible_actions)
                
        except Exception:
            return {'action': 'fold'}
    
    def _basic_hand_evaluation(self, hand: List['Card']) -> float:
        if not hand or len(hand) < 2: return 0.0
        card1, card2 = hand
        if card1.rank_value == card2.rank_value: return 0.7 + (card1.rank_value / 50.0)
        if card1.rank_value >= 10 or card2.rank_value >= 10: return 0.3 + (max(card1.rank_value, card2.rank_value) / 100.0)
        if card1.suit == card2.suit: return 0.4
        return 0.1

class NormalStrategy(AIStrategy):
    def get_action(self, player: 'Player', game: 'Game') -> Dict[str, Any]:
        try:
            possible_actions = game.get_possible_actions(player)
            if not any(possible_actions.values()): return {'action': 'fold'}
            
            hand_strength = self._evaluate_hand_strength(player, game)
            call_amount = possible_actions.get('call_amount', 0)
            stack_risk = call_amount / (player.stack + 1)

            # リスク管理
            if stack_risk > 0.3 and hand_strength < 0.5:
                return {'action': 'fold'}
            
            # 非常に強い手 (0.8以上)
            if hand_strength > 0.8:
                if possible_actions.get('can_raise', False):
                    if stack_risk < 0.5:
                        min_raise = possible_actions.get('min_raise', 100)
                        target_bet = int(min_raise * 1.5)
                        return self._get_safe_raise_action(player, possible_actions, target_bet)
                return self._get_safe_call_action(possible_actions)

            # 中程度の手
            if hand_strength > 0.4:
                if stack_risk < 0.4:
                    return self._get_safe_call_action(possible_actions)
            
            # 弱い手
            if stack_risk < 0.1:
                return self._get_safe_call_action(possible_actions)
            
            if possible_actions.get('can_check', False):
                return {'action': 'check'}

            return {'action': 'fold'}
                
        except Exception:
            return {'action': 'fold'}
    
    def _evaluate_hand_strength(self, player: 'Player', game: 'Game') -> float:
        if not player.hand: return 0.0
        c1, c2 = player.hand
        score = 0.0
        if c1.rank_value == c2.rank_value: score = 0.6 + (c1.rank_value / 40.0)
        elif c1.suit == c2.suit: score = 0.4 + (max(c1.rank_value, c2.rank_value) / 50.0)
        else: score = (c1.rank_value + c2.rank_value) / 40.0
        return min(score, 1.0)

class HardStrategy(AIStrategy):
    def get_action(self, player: 'Player', game: 'Game') -> Dict[str, Any]:
        try:
            possible_actions = game.get_possible_actions(player)
            if not any(possible_actions.values()): return {'action': 'fold'}
            
            hand_potential = self._evaluate_hand_potential(player, game)
            call_amount = possible_actions.get('call_amount', 0)
            
            # ポットサイズ
            pots = game.get_pots_info()
            pot_size = sum(p['amount'] for p in pots) if pots else 0
            pot_odds = call_amount / (pot_size + call_amount + 1)
            
            # ブレーキ
            is_high_stakes = call_amount > (player.stack * 0.4)
            if is_high_stakes and hand_potential < 0.85:
                return {'action': 'fold'}

            # 強い手
            if hand_potential > 0.7:
                if possible_actions.get('can_raise', False) and game.current_bet <= game.big_blind_amount * 2:
                    min_raise = possible_actions.get('min_raise', 100)
                    target_bet = int(pot_size * 0.7) + game.current_bet
                    # 以前の min(target_bet, max_raise) のような上限チェックは _get_safe_raise_action で行う
                    return self._get_safe_raise_action(player, possible_actions, target_bet)
                
                return self._get_safe_call_action(possible_actions)

            # 中程度の手 (ブラフ含む)
            if hand_potential > pot_odds:
                if possible_actions.get('can_raise', False) and random.random() < 0.2 and game.current_bet == 0:
                     min_raise = possible_actions.get('min_raise', 100)
                     return self._get_safe_raise_action(player, possible_actions, min_raise)
                
                return self._get_safe_call_action(possible_actions)

            if possible_actions.get('can_check', False):
                return {'action': 'check'}

            return {'action': 'fold'}
                
        except Exception:
            return {'action': 'fold'}
    
    def _evaluate_hand_potential(self, player: 'Player', game: 'Game') -> float:
        if not player.hand: return 0.0
        c1, c2 = player.hand
        score = 0.0
        if c1.rank_value == c2.rank_value:
            score = 0.6 + (c1.rank_value / 40.0)
        elif c1.suit == c2.suit and abs(c1.rank_value - c2.rank_value) == 1:
            score = 0.5 + (c1.rank_value / 100.0)
        elif c1.rank_value >= 10 and c2.rank_value >= 10:
            score = 0.5 + ((c1.rank_value + c2.rank_value) / 100.0)
        else:
            score = (c1.rank_value + c2.rank_value) / 50.0
        return min(score, 1.0)