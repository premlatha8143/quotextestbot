"""
Test script for the signal analysis engine.
This test includes mock data so you don't need live Quotex connection.
"""
import asyncio
from datetime import datetime, timedelta
import json

from ai_engine.strategies import Candle, SignalAggregator


# Mock Candle Data (simulating real market data)
def generate_mock_candles(count=200):
    """Generate realistic mock EURUSD candle data."""
    candles = []
    base_price = 1.0800
    
    for i in range(count):
        # Simulate price movement with some randomness
        open_price = base_price + (i * 0.00001) + (i % 5) * 0.00002
        close_price = open_price + (i % 3 - 1) * 0.00003
        high_price = max(open_price, close_price) + 0.00005
        low_price = min(open_price, close_price) - 0.00005
        volume = 100000 + (i % 50000)
        timestamp = int((datetime.now() - timedelta(minutes=count-i)).timestamp())
        
        candles.append(Candle(
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            timestamp=timestamp
        ))
        base_price = close_price
    
    return candles


def test_strategies_locally():
    """Test strategies with mock data (no API needed)."""
    print("=" * 70)
    print("🧪 TESTING SIGNAL ENGINE WITH MOCK DATA")
    print("=" * 70)
    
    # Generate mock candles
    print("\n📊 Generating 200 mock candles for EURUSD_otc...")
    candles = generate_mock_candles(200)
    print(f"✅ Generated {len(candles)} candles")
    print(f"   Price range: {candles[0].close:.5f} - {candles[-1].close:.5f}")
    
    # Test aggregator
    weights = {
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
    
    print("\n🔍 Analyzing signals with all 12 strategies...")
    aggregator = SignalAggregator(weights)
    
    try:
        result = aggregator.aggregate(candles)
        
        print("\n" + "=" * 70)
        print("📈 ANALYSIS RESULTS")
        print("=" * 70)
        print(f"\n🎯 Final Direction: {result['direction']} ({'BUY' if result['direction'] == 1 else 'SELL' if result['direction'] == -1 else 'NEUTRAL'})")
        print(f"💪 Confidence: {result['confidence']:.1%}")
        print(f"📊 Reason: {result['reason']}")
        print(f"\n📋 Strategy Breakdown:")
        print(f"   ✅ BUY Signals: {result['buy_count']}/12")
        print(f"   ❌ SELL Signals: {result['sell_count']}/12")
        print(f"   ⚪ NEUTRAL Signals: {result['neutral_count']}/12")
        
        print(f"\n🔬 Detailed Strategy Results:")
        print("-" * 70)
        for sig in result['signals']:
            direction_str = "🟢 BUY" if sig['direction'] == 1 else "🔴 SELL" if sig['direction'] == -1 else "⚪ NEUTRAL"
            print(f"\n{direction_str:12} | {sig['name']:25} | Strength: {sig['strength']:.3f}")
            print(f"   └─ {sig['reason']}")
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_live_connection():
    """Test with actual Quotex connection (requires credentials)."""
    import os
    from dotenv import load_dotenv
    from bot.quotex_client import QuotexClient
    from bot.signal_engine import SignalEngine
    
    load_dotenv()
    
    print("\n" + "=" * 70)
    print("🔗 TESTING WITH LIVE QUOTEX CONNECTION")
    print("=" * 70)
    
    email = os.getenv("QUOTEX_EMAIL")
    password = os.getenv("QUOTEX_PASSWORD")
    
    if not email or not password:
        print("❌ QUOTEX_EMAIL or QUOTEX_PASSWORD not set in .env")
        print("   Skipping live connection test")
        return False
    
    print(f"\n🔐 Connecting to Quotex as {email}...")
    client = QuotexClient(email, password)
    
    ok = await client.connect()
    if not ok:
        print("❌ Connection failed!")
        return False
    
    print("✅ Connected successfully!")
    
    try:
        balance = await client.get_balance()
        print(f"💰 Account Balance: {balance}")
        
        print("\n📊 Fetching live candles...")
        engine = SignalEngine(client)
        result = await engine.analyze()
        
        if result is None:
            print("❌ No result returned")
            return False
        
        print("\n" + "=" * 70)
        print("📈 LIVE SIGNAL ANALYSIS RESULTS")
        print("=" * 70)
        print(f"\n🎯 Direction: {result.get('direction')} ({'BUY' if result.get('direction') == 1 else 'SELL' if result.get('direction') == -1 else 'NEUTRAL'})")
        print(f"💪 Confidence: {result.get('confidence', 0):.1%}")
        print(f"📊 Reason: {result.get('reason', 'N/A')}")
        print(f"\n   ✅ BUY Count: {result.get('buy_count', 0)}")
        print(f"   ❌ SELL Count: {result.get('sell_count', 0)}")
        print(f"   ⚪ NEUTRAL Count: {result.get('neutral_count', 0)}")
        
        print("\n" + "=" * 70)
        print("✅ LIVE TEST COMPLETED!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during live test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected from Quotex")


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🤖 QUOTEX SIGNAL ENGINE TEST SUITE".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Test 1: Mock data (always works)
    test1_passed = test_strategies_locally()
    
    # Test 2: Live connection (requires credentials)
    print("\n")
    try:
        test2_passed = await test_with_live_connection()
    except Exception as e:
        print(f"⚠️  Skipping live test: {e}")
        test2_passed = None
    
    # Summary
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " TEST SUMMARY ".center(68, "=") + "║")
    print("╠" + "=" * 68 + "╣")
    print(f"║ Mock Data Test:        {'✅ PASSED' if test1_passed else '❌ FAILED':50} ║")
    if test2_passed is not None:
        print(f"║ Live Connection Test:  {'✅ PASSED' if test2_passed else '❌ FAILED':50} ║")
    else:
        print(f"║ Live Connection Test:  {'⏭️  SKIPPED':50} ║")
    print("╚" + "=" * 68 + "╝\n")


if __name__ == "__main__":
    asyncio.run(main())
