"""
Quotex Auto Trading Bot - Strategy Engine
Contains 12 professional trading strategies. Each returns:
  1  = BUY (UP)
 -1  = SELL (DOWN)
  0  = NO SIGNAL
"""

import math
from collections import namedtuple

Candle = namedtuple("Candle", ["open", "high", "low", "close", "volume", "timestamp"])
Signal = namedtuple("Signal", ["direction", "strength", "name", "reason"])


def _ema(values: list, period: int) -> list:
    """Exponential Moving Average."""
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    ema = [sum(values[:period]) / period]
    for price in values[period:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema


def _sma(values: list, period: int) -> list:
    """Simple Moving Average."""
    return [sum(values[i:i+period]) / period for i in range(len(values) - period + 1)]


def _rsi(closes: list, period: int = 14) -> list:
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return []
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsis = []
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsis.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsis.append(100 - 100 / (1 + rs))
    return rsis


def _atr(candles: list, period: int = 14) -> list:
    """Average True Range."""
    if len(candles) < period + 1:
        return []
    trs = []
    for i in range(1, len(candles)):
        hl = candles[i].high - candles[i].low
        hpc = abs(candles[i].high - candles[i-1].close)
        lpc = abs(candles[i].low - candles[i-1].close)
        trs.append(max(hl, hpc, lpc))
    atrs = [sum(trs[:period]) / period]
    for tr in trs[period:]:
        atrs.append((atrs[-1] * (period - 1) + tr) / period)
    return atrs


def _stddev(values: list, period: int) -> list:
    """Standard deviation over rolling window."""
    result = []
    for i in range(period - 1, len(values)):
        window = values[i - period + 1:i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        result.append(math.sqrt(variance))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 1: Trend Detection (EMA Direction)
# ─────────────────────────────────────────────────────────────────────────────
class TrendDetection:
    NAME = "TrendDetection"

    def analyze(self, candles: list) -> Signal:
        closes = [c.close for c in candles]
        ema20 = _ema(closes, 20)
        ema50 = _ema(closes, 50)
        if len(ema20) < 3 or len(ema50) < 3:
            return Signal(0, 0, self.NAME, "Insufficient data")

        # Uptrend: EMA20 > EMA50 and both rising
        if ema20[-1] > ema50[-1] and ema20[-1] > ema20[-2]:
            strength = min(abs(ema20[-1] - ema50[-1]) / ema50[-1] * 1000, 1.0)
            return Signal(1, strength, self.NAME, f"Uptrend EMA20>{ema50[-1]:.4f}")
        # Downtrend: EMA20 < EMA50 and both falling
        elif ema20[-1] < ema50[-1] and ema20[-1] < ema20[-2]:
            strength = min(abs(ema50[-1] - ema20[-1]) / ema50[-1] * 1000, 1.0)
            return Signal(-1, strength, self.NAME, f"Downtrend EMA20<{ema50[-1]:.4f}")
        return Signal(0, 0, self.NAME, "No clear trend")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 2: Support & Resistance Levels
# ─────────────────────────────────────────────────────────────────────────────
class SupportResistance:
    NAME = "SupportResistance"

    def _find_levels(self, candles, window=5):
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        resistance, support = [], []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                resistance.append(highs[i])
            if lows[i] == min(lows[i-window:i+window+1]):
                support.append(lows[i])
        return support[-3:] if support else [], resistance[-3:] if resistance else []

    def analyze(self, candles: list) -> Signal:
        if len(candles) < 20:
            return Signal(0, 0, self.NAME, "Insufficient data")
        support, resistance = self._find_levels(candles)
        price = candles[-1].close
        if not support or not resistance:
            return Signal(0, 0, self.NAME, "No levels found")

        nearest_sup = max(support) if support else None
        nearest_res = min(resistance) if resistance else None
        margin = (candles[-1].high - candles[-1].low) * 0.5

        if nearest_sup and abs(price - nearest_sup) < margin:
            return Signal(1, 0.8, self.NAME, f"Near support {nearest_sup:.4f}")
        if nearest_res and abs(price - nearest_res) < margin:
            return Signal(-1, 0.8, self.NAME, f"Near resistance {nearest_res:.4f}")
        return Signal(0, 0, self.NAME, "Not at key level")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 3: RSI Momentum
# ─────────────────────────────────────────────────────────────────────────────
class RSIMomentum:
    NAME = "RSIMomentum"

    def analyze(self, candles: list) -> Signal:
        closes = [c.close for c in candles]
        rsi = _rsi(closes, 14)
        if len(rsi) < 3:
            return Signal(0, 0, self.NAME, "Insufficient RSI data")

        current_rsi = rsi[-1]
        prev_rsi = rsi[-2]

        # Oversold bounce
        if current_rsi < 30:
            strength = (30 - current_rsi) / 30
            return Signal(1, min(strength, 1.0), self.NAME, f"RSI oversold {current_rsi:.1f}")
        # Overbought reversal
        if current_rsi > 70:
            strength = (current_rsi - 70) / 30
            return Signal(-1, min(strength, 1.0), self.NAME, f"RSI overbought {current_rsi:.1f}")
        # RSI crossing midline
        if prev_rsi < 50 < current_rsi:
            return Signal(1, 0.5, self.NAME, f"RSI crossed 50 up {current_rsi:.1f}")
        if prev_rsi > 50 > current_rsi:
            return Signal(-1, 0.5, self.NAME, f"RSI crossed 50 down {current_rsi:.1f}")
        return Signal(0, 0, self.NAME, f"RSI neutral {current_rsi:.1f}")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 4: Moving Average Crossover (Fast/Slow EMA)
# ─────────────────────────────────────────────────────────────────────────────
class MovingAverageCrossover:
    NAME = "MovingAverageCrossover"

    def analyze(self, candles: list) -> Signal:
        closes = [c.close for c in candles]
        fast = _ema(closes, 9)
        slow = _ema(closes, 21)
        if len(fast) < 3 or len(slow) < 3:
            return Signal(0, 0, self.NAME, "Insufficient data")

        # Align lengths
        diff = len(fast) - len(slow)
        fast = fast[diff:] if diff > 0 else fast
        slow = slow[-diff:] if diff < 0 else slow

        # Golden cross (fast crosses above slow)
        if fast[-2] <= slow[-2] and fast[-1] > slow[-1]:
            return Signal(1, 0.9, self.NAME, "Golden cross (9EMA > 21EMA)")
        # Death cross (fast crosses below slow)
        if fast[-2] >= slow[-2] and fast[-1] < slow[-1]:
            return Signal(-1, 0.9, self.NAME, "Death cross (9EMA < 21EMA)")
        # Trend confirmation
        if fast[-1] > slow[-1]:
            strength = min(abs(fast[-1] - slow[-1]) / slow[-1] * 500, 0.6)
            return Signal(1, strength, self.NAME, "Fast above slow")
        strength = min(abs(slow[-1] - fast[-1]) / slow[-1] * 500, 0.6)
        return Signal(-1, strength, self.NAME, "Fast below slow")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 5: Candlestick Pattern Recognition
# ─────────────────────────────────────────────────────────────────────────────
class CandlestickPattern:
    NAME = "CandlestickPattern"

    def _body(self, c): return abs(c.close - c.open)
    def _range(self, c): return c.high - c.low
    def _upper_wick(self, c): return c.high - max(c.open, c.close)
    def _lower_wick(self, c): return min(c.open, c.close) - c.low
    def _is_bull(self, c): return c.close > c.open
    def _is_bear(self, c): return c.close < c.open

    def analyze(self, candles: list) -> Signal:
        if len(candles) < 3:
            return Signal(0, 0, self.NAME, "Insufficient data")
        c0, c1, c2 = candles[-3], candles[-2], candles[-1]
        b2 = self._body(c2)
        r2 = self._range(c2)
        b1 = self._body(c1)

        # Doji (indecision before reversal)
        if r2 > 0 and b2 / r2 < 0.1:
            trend = "up" if c1.close > c0.close else "down"
            if trend == "up":
                return Signal(-1, 0.7, self.NAME, "Doji after uptrend → reversal")
            return Signal(1, 0.7, self.NAME, "Doji after downtrend → reversal")

        # Hammer (bullish reversal at bottom)
        lw = self._lower_wick(c2)
        uw = self._upper_wick(c2)
        if b2 > 0 and lw >= 2 * b2 and uw <= b2 * 0.3 and self._is_bull(c2):
            return Signal(1, 0.85, self.NAME, "Hammer → bullish reversal")

        # Shooting star (bearish reversal at top)
        if b2 > 0 and uw >= 2 * b2 and lw <= b2 * 0.3 and self._is_bear(c2):
            return Signal(-1, 0.85, self.NAME, "Shooting star → bearish reversal")

        # Bullish engulfing
        if (self._is_bear(c1) and self._is_bull(c2)
                and c2.open <= c1.close and c2.close >= c1.open):
            return Signal(1, 0.9, self.NAME, "Bullish engulfing")

        # Bearish engulfing
        if (self._is_bull(c1) and self._is_bear(c2)
                and c2.open >= c1.close and c2.close <= c1.open):
            return Signal(-1, 0.9, self.NAME, "Bearish engulfing")

        # Three white soldiers (strong uptrend)
        if all(self._is_bull(c) for c in [c0, c1, c2]):
            if c1.close > c0.close and c2.close > c1.close:
                return Signal(1, 0.8, self.NAME, "Three white soldiers")

        # Three black crows (strong downtrend)
        if all(self._is_bear(c) for c in [c0, c1, c2]):
            if c1.close < c0.close and c2.close < c1.close:
                return Signal(-1, 0.8, self.NAME, "Three black crows")

        return Signal(0, 0, self.NAME, "No pattern")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 6: Breakout Detection
# ─────────────────────────────────────────────────────────────────────────────
class BreakoutDetection:
    NAME = "BreakoutDetection"

    def analyze(self, candles: list) -> Signal:
        if len(candles) < 20:
            return Signal(0, 0, self.NAME, "Insufficient data")
        lookback = candles[-20:-1]
        recent_high = max(c.high for c in lookback)
        recent_low = min(c.low for c in lookback)
        current = candles[-1]
        atr = _atr(candles, 14)
        threshold = atr[-1] * 0.5 if atr else 0

        if current.close > recent_high + threshold:
            strength = min((current.close - recent_high) / atr[-1], 1.0) if atr else 0.7
            return Signal(1, strength, self.NAME, f"Upside breakout above {recent_high:.4f}")
        if current.close < recent_low - threshold:
            strength = min((recent_low - current.close) / atr[-1], 1.0) if atr else 0.7
            return Signal(-1, strength, self.NAME, f"Downside breakout below {recent_low:.4f}")
        return Signal(0, 0, self.NAME, "No breakout")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 7: Reversal Pattern (Higher High / Lower Low exhaustion)
# ─────────────────────────────────────────────────────────────────────────────
class ReversalPattern:
    NAME = "ReversalPattern"

    def analyze(self, candles: list) -> Signal:
        if len(candles) < 10:
            return Signal(0, 0, self.NAME, "Insufficient data")
        closes = [c.close for c in candles[-10:]]
        highs = [c.high for c in candles[-10:]]
        lows = [c.low for c in candles[-10:]]

        # Bullish: lower lows followed by higher close
        if lows[-1] > lows[-2] and lows[-2] < lows[-3] and closes[-1] > closes[-2]:
            return Signal(1, 0.75, self.NAME, "Bullish reversal: higher low forming")

        # Bearish: higher highs followed by lower close
        if highs[-1] < highs[-2] and highs[-2] > highs[-3] and closes[-1] < closes[-2]:
            return Signal(-1, 0.75, self.NAME, "Bearish reversal: lower high forming")

        # Double bottom (W pattern)
        if (abs(lows[-7] - lows[-3]) / lows[-3] < 0.001
                and closes[-1] > max(closes[-6:-4])):
            return Signal(1, 0.85, self.NAME, "Double bottom (W)")

        # Double top (M pattern)
        if (abs(highs[-7] - highs[-3]) / highs[-3] < 0.001
                and closes[-1] < min(closes[-6:-4])):
            return Signal(-1, 0.85, self.NAME, "Double top (M)")

        return Signal(0, 0, self.NAME, "No reversal pattern")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 8: Volatility Filter (ATR-based)
# ─────────────────────────────────────────────────────────────────────────────
class VolatilityFilter:
    NAME = "VolatilityFilter"

    def analyze(self, candles: list) -> Signal:
        if len(candles) < 20:
            return Signal(0, 0, self.NAME, "Insufficient data")
        atr = _atr(candles, 14)
        if not atr:
            return Signal(0, 0, self.NAME, "No ATR")

        atr_now = atr[-1]
        atr_avg = sum(atr[-10:]) / 10

        # Low volatility: potential breakout ahead — signal neutral
        if atr_now < atr_avg * 0.7:
            return Signal(0, 0, self.NAME, "Low volatility – wait for breakout")

        # High volatility squeeze release → follow last candle direction
        if atr_now > atr_avg * 1.5:
            last = candles[-1]
            if last.close > last.open:
                return Signal(1, 0.65, self.NAME, f"High vol squeeze → UP ATR={atr_now:.5f}")
            return Signal(-1, 0.65, self.NAME, f"High vol squeeze → DOWN ATR={atr_now:.5f}")

        return Signal(0, 0, self.NAME, "Neutral volatility")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 9: Bollinger Bands
# ─────────────────────────────────────────────────────────────────────────────
class BollingerBands:
    NAME = "BollingerBands"

    def analyze(self, candles: list) -> Signal:
        closes = [c.close for c in candles]
        period = 20
        if len(closes) < period:
            return Signal(0, 0, self.NAME, "Insufficient data")

        sma = _sma(closes, period)
        std = _stddev(closes, period)
        if not sma or not std:
            return Signal(0, 0, self.NAME, "Calc error")

        mid = sma[-1]
        dev = std[-1]
        upper = mid + 2 * dev
        lower = mid - 2 * dev
        price = closes[-1]

        # Price at lower band → mean reversion UP
        if price <= lower:
            strength = min((lower - price) / dev, 1.0)
            return Signal(1, strength, self.NAME, f"At lower BB {lower:.4f}")
        # Price at upper band → mean reversion DOWN
        if price >= upper:
            strength = min((price - upper) / dev, 1.0)
            return Signal(-1, strength, self.NAME, f"At upper BB {upper:.4f}")
        # Band squeeze (low std) — no trade
        if dev / mid < 0.001:
            return Signal(0, 0, self.NAME, "BB squeeze – waiting")
        return Signal(0, 0, self.NAME, f"Inside bands ({lower:.4f}–{upper:.4f})")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 10: MACD
# ─────────────────────────────────────────────────────────────────────────────
class MACDStrategy:
    NAME = "MACDStrategy"

    def analyze(self, candles: list) -> Signal:
        closes = [c.close for c in candles]
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)
        if len(ema12) < 10 or len(ema26) < 10:
            return Signal(0, 0, self.NAME, "Insufficient data")

        diff = len(ema12) - len(ema26)
        ema12 = ema12[diff:]
        macd_line = [a - b for a, b in zip(ema12, ema26)]
        signal_line = _ema(macd_line, 9)
        if len(signal_line) < 3:
            return Signal(0, 0, self.NAME, "Insufficient signal data")

        diff_ml = len(macd_line) - len(signal_line)
        macd_trimmed = macd_line[diff_ml:]
        histogram = [m - s for m, s in zip(macd_trimmed, signal_line)]

        # MACD crossing signal line up
        if macd_trimmed[-2] <= signal_line[-2] and macd_trimmed[-1] > signal_line[-1]:
            return Signal(1, 0.88, self.NAME, "MACD bullish crossover")
        # MACD crossing signal line down
        if macd_trimmed[-2] >= signal_line[-2] and macd_trimmed[-1] < signal_line[-1]:
            return Signal(-1, 0.88, self.NAME, "MACD bearish crossover")
        # Histogram momentum
        if len(histogram) >= 3 and histogram[-1] > histogram[-2] > histogram[-3] > 0:
            return Signal(1, 0.6, self.NAME, "MACD histogram rising")
        if len(histogram) >= 3 and histogram[-1] < histogram[-2] < histogram[-3] < 0:
            return Signal(-1, 0.6, self.NAME, "MACD histogram falling")

        return Signal(0, 0, self.NAME, "No MACD signal")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 11: Stochastic Oscillator
# ─────────────────────────────────────────────────────────────────────────────
class StochasticOscillator:
    NAME = "StochasticOscillator"

    def _stoch(self, candles, k_period=14, d_period=3):
        if len(candles) < k_period:
            return [], []
        k_values = []
        for i in range(k_period - 1, len(candles)):
            window = candles[i - k_period + 1:i + 1]
            highest = max(c.high for c in window)
            lowest = min(c.low for c in window)
            c_price = candles[i].close
            k = ((c_price - lowest) / (highest - lowest) * 100) if highest != lowest else 50
            k_values.append(k)
        d_values = _sma(k_values, d_period)
        return k_values, d_values

    def analyze(self, candles: list) -> Signal:
        k, d = self._stoch(candles)
        if len(k) < 3 or len(d) < 3:
            return Signal(0, 0, self.NAME, "Insufficient data")

        diff = len(k) - len(d)
        k = k[diff:]

        # Oversold: K < 20 and crosses above D
        if k[-1] < 20 and k[-1] > d[-1] and k[-2] <= d[-2]:
            return Signal(1, 0.82, self.NAME, f"Stoch oversold crossup K={k[-1]:.1f}")
        # Overbought: K > 80 and crosses below D
        if k[-1] > 80 and k[-1] < d[-1] and k[-2] >= d[-2]:
            return Signal(-1, 0.82, self.NAME, f"Stoch overbought crossdown K={k[-1]:.1f}")
        if k[-1] < 20:
            return Signal(1, 0.55, self.NAME, f"Stoch oversold K={k[-1]:.1f}")
        if k[-1] > 80:
            return Signal(-1, 0.55, self.NAME, f"Stoch overbought K={k[-1]:.1f}")
        return Signal(0, 0, self.NAME, f"Stoch neutral K={k[-1]:.1f}")


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 12: Volume Analysis (relative volume spike)
# ─────────────────────────────────────────────────────────────────────────────
class VolumeAnalysis:
    NAME = "VolumeAnalysis"

    def analyze(self, candles: list) -> Signal:
        if len(candles) < 15:
            return Signal(0, 0, self.NAME, "Insufficient data")
        volumes = [c.volume for c in candles]
        avg_vol = sum(volumes[-15:-1]) / 14
        curr_vol = volumes[-1]
        last = candles[-1]

        if avg_vol == 0:
            return Signal(0, 0, self.NAME, "No volume data")

        vol_ratio = curr_vol / avg_vol
        if vol_ratio > 2.0:  # Volume spike
            if last.close > last.open:
                return Signal(1, min(vol_ratio / 4, 1.0), self.NAME,
                              f"Vol spike ×{vol_ratio:.1f} bullish")
            return Signal(-1, min(vol_ratio / 4, 1.0), self.NAME,
                          f"Vol spike ×{vol_ratio:.1f} bearish")
        return Signal(0, 0, self.NAME, f"Normal volume ratio={vol_ratio:.1f}")


# ─────────────────────────────────────────────────────────────────────────────
# Signal Aggregator
# ─────────────────────────────────────────────────────────────────────────────
class SignalAggregator:
    """Combines all strategies into a single weighted decision."""

    def __init__(self, weights: dict):
        self.strategies = [
            TrendDetection(), SupportResistance(), RSIMomentum(),
            MovingAverageCrossover(), CandlestickPattern(), BreakoutDetection(),
            ReversalPattern(), VolatilityFilter(), BollingerBands(),
            MACDStrategy(), StochasticOscillator(), VolumeAnalysis(),
        ]
        self.weights = weights

    def aggregate(self, candles: list, min_agreement: int = 6) -> dict:
        """Run all strategies and return aggregate decision."""
        signals = []
        for strategy in self.strategies:
            try:
                sig = strategy.analyze(candles)
                signals.append(sig)
            except Exception as e:
                signals.append(Signal(0, 0, strategy.NAME, f"Error: {e}"))

        buy_score = sum(
            s.strength * self.weights.get(s.name, 1.0)
            for s in signals if s.direction == 1
        )
        sell_score = sum(
            s.strength * self.weights.get(s.name, 1.0)
            for s in signals if s.direction == -1
        )
        buy_count = sum(1 for s in signals if s.direction == 1)
        sell_count = sum(1 for s in signals if s.direction == -1)

        total_weight = sum(self.weights.get(s.name, 1.0) for s in signals)
        max_score = total_weight

        direction = 0
        confidence = 0.0
        reason = "No consensus"

        if buy_count >= min_agreement and buy_score > sell_score:
            direction = 1
            confidence = round(buy_score / max_score, 3)
            reason = f"{buy_count} strategies agree → UP"
        elif sell_count >= min_agreement and sell_score > buy_score:
            direction = -1
            confidence = round(sell_score / max_score, 3)
            reason = f"{sell_count} strategies agree → DOWN"

        return {
            "direction": direction,
            "confidence": confidence,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "neutral_count": sum(1 for s in signals if s.direction == 0),
            "reason": reason,
            "signals": [
                {"name": s.name, "direction": s.direction,
                 "strength": round(s.strength, 3), "reason": s.reason}
                for s in signals
            ],
        }
