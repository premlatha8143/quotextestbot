"""
Quotex Auto Trading Bot - Configuration
Adjust these settings before running the bot.
"""

CONFIG = {
    # ─── Quotex Platform ─────────────────────────────────────────────
    "quotex_url": "https://quotex.io/en/sign-in",
    "headless": False,           # Set True to run browser in background

    # ─── Trade Settings ──────────────────────────────────────────────
    "trade_amount": 1,           # Amount per trade in USD
    "expiry_time": 60,           # Expiry in seconds (60 = 1 min)
    "currency_pair": "auto",     # "auto" detects active pair, or set e.g. "EUR/USD"

    # ─── Signal Engine ───────────────────────────────────────────────
    "min_confidence": 0.65,      # Min confidence score (0.0 – 1.0)
    "min_strategy_agreement": 6, # Min strategies that must agree (out of 10+)
    "candle_history": 50,        # Number of historical candles to analyze
    "signal_interval": 5,        # Seconds between signal checks

    # ─── Risk Management ─────────────────────────────────────────────
    "max_trades_per_session": 25,
    "stop_loss_limit": 15,       # Max total loss ($) before bot stops
    "daily_profit_target": 30,   # Bot pauses after hitting this profit ($)
    "cooldown_seconds": 30,      # Wait time between trades (seconds)
    "max_consecutive_losses": 3, # Stop after N consecutive losses

    # ─── Martingale (Optional) ────────────────────────────────────────
    "martingale_enabled": False,
    "martingale_multiplier": 2.0,
    "martingale_max_steps": 3,

    # ─── Dashboard ───────────────────────────────────────────────────
    "dashboard_host": "127.0.0.1",
    "dashboard_port": 5000,
    "dashboard_debug": False,

    # ─── Logging ─────────────────────────────────────────────────────
    "log_file": "quotex_bot.log",
    "log_level": "INFO",
}

STRATEGY_WEIGHTS = {
    "TrendDetection":        1.2,
    "SupportResistance":     1.0,
    "RSIMomentum":           1.1,
    "MovingAverageCrossover":1.0,
    "CandlestickPattern":    1.3,
    "BreakoutDetection":     1.0,
    "ReversalPattern":       1.0,
    "VolatilityFilter":      0.8,
    "BollingerBands":        1.0,
    "MACDStrategy":          1.1,
    "StochasticOscillator":  0.9,
    "VolumeAnalysis":        0.7,
}
