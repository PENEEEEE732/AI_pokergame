class PokerException(Exception):
    """ポーカーゲームロジックのベースとなるカスタム例外クラス。"""
    pass

class InvalidActionException(PokerException):
    """プレイヤーが無効なアクションを試みた場合に送出される例外。"""
    pass

class NotPlayerTurnException(PokerException):
    """自分のターンではないプレイヤーがアクションを試みた場合に送出される例外。"""
    pass

class GameLogicException(PokerException):
    """ゲームの進行に関する一般的なロジックエラー。"""
    pass

class InsufficientChipsException(PokerException):
    """プレイヤーのチップが不足している場合に送出される例外。"""
    pass