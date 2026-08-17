from ai_engine.strategies import Candle, SignalAggregator


class SignalEngine:
    def __init__(self, client):
        self.client = client

        # Equal weight for all strategies initially
        self.weights = {
            "TrendDetection": 1.0,
            "SupportResistance": 1.0,
            "RSIMomentum": 1.0,
            "MovingAverageCrossover": 1.0,
            "CandlestickPattern": 1.0,
            "BreakoutDetection": 1.0,
            "ReversalPattern": 1.0,
            "VolatilityFilter": 1.0,
            "BollingerBands": 1.0,
            "MACDStrategy": 1.0,
            "StochasticOscillator": 1.0,
            "VolumeAnalysis": 1.0,
        }

        self.aggregator = SignalAggregator(self.weights)

    async def analyze(
        self,
        asset="EURUSD_otc",
        timeframe=60,
        candles_count=200,
    ):
        """
        Download candles from Quotex and return AI signal.
        """

        raw = await self.client.get_candles(
            asset=asset,
            timeframe=timeframe,
            count=candles_count,
        )

        if not raw:
            print(f"ERROR: No candles returned for {asset}")
            return {"direction": 0, "confidence": 0, "reason": "No candle data"}

        candles = []

        for c in raw:
            try:
                candles.append(
                    Candle(
                        open=float(c["open"]),
                        high=float(c["high"]),
                        low=float(c["low"]),
                        close=float(c["close"]),
                        volume=float(c.get("volume", 0)),
                        timestamp=c["time"],
                    )
                )
            except (KeyError, TypeError, ValueError) as e:
                print(f"ERROR parsing candle: {c} - {e}")
                continue

        if len(candles) < 20:
            print(f"WARNING: Only {len(candles)} candles available (need ≥20)")
            return {"direction": 0, "confidence": 0, "reason": f"Insufficient data: {len(candles)} candles"}

        try:
            result = self.aggregator.aggregate(candles)
            return result
        except Exception as e:
            print(f"ERROR in aggregator: {e}")
            return {"direction": 0, "confidence": 0, "reason": f"Aggregation error: {str(e)}"}
