"""
Quotex Auto Trading Bot - Risk Manager
Enforces all safety rules and session limits.
"""

import time
from datetime import datetime, date


class RiskManager:
    def __init__(self, config: dict):
        self.config = config
        self.reset_session()
        self.session_date = date.today()

    def reset_session(self):
        self.trades_placed = 0
        self.total_pnl = 0.0
        self.consecutive_losses = 0
        self.last_trade_time = 0
        self.trade_history = []
        self.current_trade_amount = self.config["trade_amount"]
        self.martingale_step = 0
        self.is_active = True
        self.stop_reason = None

    def _check_daily_reset(self):
        today = date.today()
        if today != self.session_date:
            self.session_date = today
            self.reset_session()

    def can_trade(self) -> tuple[bool, str]:
        """Returns (allowed, reason). Call before placing any trade."""
        self._check_daily_reset()

        if not self.is_active:
            return False, f"Bot stopped: {self.stop_reason}"

        # Max trades per session
        if self.trades_placed >= self.config["max_trades_per_session"]:
            self.is_active = False
            self.stop_reason = f"Max trades reached ({self.config['max_trades_per_session']})"
            return False, self.stop_reason

        # Stop loss limit
        if self.total_pnl <= -abs(self.config["stop_loss_limit"]):
            self.is_active = False
            self.stop_reason = f"Stop loss hit (loss=${abs(self.total_pnl):.2f})"
            return False, self.stop_reason

        # Daily profit target
        if self.total_pnl >= self.config["daily_profit_target"]:
            self.is_active = False
            self.stop_reason = f"Daily profit target reached (${self.total_pnl:.2f})"
            return False, self.stop_reason

        # Consecutive losses
        if self.consecutive_losses >= self.config["max_consecutive_losses"]:
            self.is_active = False
            self.stop_reason = f"Max consecutive losses ({self.consecutive_losses})"
            return False, self.stop_reason

        # Cooldown between trades
        elapsed = time.time() - self.last_trade_time
        if elapsed < self.config["cooldown_seconds"] and self.last_trade_time > 0:
            remaining = int(self.config["cooldown_seconds"] - elapsed)
            return False, f"Cooldown: {remaining}s remaining"

        return True, "OK"

    def get_trade_amount(self) -> float:
        """Returns trade amount, applying Martingale if enabled."""
        if not self.config.get("martingale_enabled"):
            return self.config["trade_amount"]
        return self.current_trade_amount

    def record_trade_open(self, direction: int, amount: float,
                          pair: str, expiry: int, confidence: float):
        """Called when a trade is placed."""
        trade = {
            "id": len(self.trade_history) + 1,
            "pair": pair,
            "direction": "UP" if direction == 1 else "DOWN",
            "amount": amount,
            "expiry": expiry,
            "confidence": confidence,
            "open_time": datetime.now().strftime("%H:%M:%S"),
            "status": "open",
            "pnl": 0.0,
        }
        self.trade_history.append(trade)
        self.last_trade_time = time.time()
        self.trades_placed += 1
        return trade["id"]

    def record_trade_close(self, trade_id: int, won: bool):
        """Called when a trade result comes in."""
        for t in self.trade_history:
            if t["id"] == trade_id:
                amount = t["amount"]
                if won:
                    pnl = amount * 0.85  # ~85% payout
                    t["pnl"] = pnl
                    t["status"] = "WIN"
                    self.total_pnl += pnl
                    self.consecutive_losses = 0
                    # Reset martingale on win
                    if self.config.get("martingale_enabled"):
                        self.current_trade_amount = self.config["trade_amount"]
                        self.martingale_step = 0
                else:
                    pnl = -amount
                    t["pnl"] = pnl
                    t["status"] = "LOSS"
                    self.total_pnl += pnl
                    self.consecutive_losses += 1
                    # Apply martingale on loss
                    if (self.config.get("martingale_enabled")
                            and self.martingale_step < self.config["martingale_max_steps"]):
                        self.current_trade_amount *= self.config["martingale_multiplier"]
                        self.martingale_step += 1
                break

    def get_stats(self) -> dict:
        wins = sum(1 for t in self.trade_history if t["status"] == "WIN")
        losses = sum(1 for t in self.trade_history if t["status"] == "LOSS")
        total_closed = wins + losses
        win_rate = (wins / total_closed * 100) if total_closed else 0
        return {
            "trades_placed": self.trades_placed,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "total_pnl": round(self.total_pnl, 2),
            "consecutive_losses": self.consecutive_losses,
            "is_active": self.is_active,
            "stop_reason": self.stop_reason,
            "trade_amount": self.get_trade_amount(),
        }
