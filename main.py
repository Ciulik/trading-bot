import requests
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from predictor import PricePredictor

# Show all columns
pd.set_option('display.max_columns', None)


def fetch_historical_data(symbol, days=30, interval='1h', timeout=5):
    """
    Fetch historical price data from Binance
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        days: Number of days to fetch
        interval: Candle interval ('1m', '5m', '15m', '1h', etc.)
        timeout: Request timeout in seconds
    
    Returns:
        DataFrame with timestamps and prices, or None if error
    """
    api_url = "https://api.binance.com/api/v3/klines"

    # Calculate limit based on interval
    interval_limits = {
        '1m': 24 * 60 * days,
        '5m': 24 * 12 * days,
        '15m': 24 * 4 * days,
        '1h': 24 * days,
        '4h': 6 * days,
        '1d': days
    }

    limit = interval_limits.get(interval, 24 * days)

    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close',
                                         'volume', 'close_time', 'quote_asset_volume',
                                         'number_of_trades', 'taker_buy_base',
                                         'taker_buy_quote', 'ignore'])

        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        return df[['timestamp', 'close','volume']]
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return None


def save_prices_to_file(prices, volumes,filename="prices.json"):
    """Save prices to a JSON file"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "count": len(prices),
        "prices": prices,
        "volumes": volumes
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved {len(prices)} prices to {filename}")


def load_prices_from_file(filename="prices.json"):
    """Load prices from a JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded {data['count']} prices from {filename}")
        return data['prices'], data.get('volumes',None)
    except FileNotFoundError:
        print(f"✗ File {filename} not found")
        return None, None


def validate_prediction(predicted_price, actual_price):
    """
    Compare predicted vs actual price
    
    Args:
        predicted_price: Price the model predicted
        actual_price: Actual price that occurred
    
    Returns:
        dict with error information
    """
    error = abs(predicted_price - actual_price)
    error_percent = (error / actual_price) * 100
    
    return {
        "predicted": predicted_price,
        "actual": actual_price,
        "error": error,
        "error_percent": error_percent
    }


def save_validation_log(validation_data, filename="validation_log.json"):
    """Save validation result to log file"""
    try:
        with open(filename, 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        log = []
    
    log.append(validation_data)
    
    with open(filename, 'w') as f:
        json.dump(log, f, indent=2)

    """
    old linear regression function might use later
def live_prediction_validation(predictor, prices, interval='1m', wait_minutes=1):
    
    Make a live prediction, wait for next candle, then validate
    
    Args:
        predictor: Trained PricePredictor
        prices: List of prices
        interval: Candle interval
        wait_minutes: How long to wait for next candle
    
    Returns:
        dict with validation results
    
    print("\n" + "="*70)
    print(f"LIVE PREDICTION VALIDATION")
    print(f"Interval: {interval} | Wait time: {wait_minutes} minute(s)")
    print("="*70)
    
    # Make prediction
    predicted, confidence = predictor.predict(prices)
    current_price = prices[-1]
    expected_change = ((predicted - current_price) / current_price) * 100
    
    prediction_time = datetime.now()
    
    print(f"\n[PREDICTION TIME] {prediction_time.strftime('%H:%M:%S')}")
    print(f"Current price:   ${current_price:.2f}")
    print(f"Predicted price: ${predicted:.2f}")
    print(f"Expected change: {expected_change:+.2f}%")
    print(f"Confidence:      {confidence:.2%}")
    
    # Wait for next candle
    wait_seconds = wait_minutes * 60
    print(f"\n⏳ Waiting {wait_minutes} minute(s) for next candle to close...")
    print("-" * 70)
    
    # Countdown timer
    for i in range(wait_seconds, 0, -1):
        minutes_left = i // 60
        seconds_left = i % 60
        print(f"⏱️  {minutes_left:02d}:{seconds_left:02d} remaining...", end='\r')
        time.sleep(1)
    
    print("\n✓ Next candle has closed! Fetching new data...")
    
    # Fetch new data
    df = fetch_historical_data('BTCUSDT', days=1, interval=interval)
    
    if df is None:
        print("✗ Failed to fetch new data")
        return None
    
    new_prices = df['close'].tolist()
    actual_next_price = new_prices[-1]
    validation_time = datetime.now()
    
    # Calculate error
    error = abs(predicted - actual_next_price)
    error_percent = (error / actual_next_price) * 100
    actual_change = ((actual_next_price - current_price) / current_price) * 100
    
    # Determine if prediction was correct
    if error_percent < 0.01:
        result = "✅ EXCELLENT"
        accuracy = "Very accurate!"
    elif error_percent < 0.07:
        result = " VERY GOOD"
        accuracy = "Highly accurate!"
    elif error_percent < 0.13:
        result = " GOOD"
        accuracy = "Accurate!"
    elif error_percent < 0.2:
        result = "⚠️  OKAY"
        accuracy = "Close enough"
    else:
        result = "❌ POOR"
        accuracy = "Prediction was off"
    
    # Display results
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    print(f"[VALIDATION TIME] {validation_time.strftime('%H:%M:%S')}")
    print(f"\nPrice Comparison:")
    print(f"  Predicted price: ${predicted:.2f}")
    print(f"  Actual price:    ${actual_next_price:.2f}")
    print(f"  Error:           ${error:.2f} ({error_percent:.2f}%)")
    print(f"\nDirection:")
    print(f"  Expected change: {expected_change:+.2f}%")
    print(f"  Actual change:   {actual_change:+.2f}%")
    
    # Check if direction was correct
    direction_correct = (expected_change > 0 and actual_change > 0) or (expected_change < 0 and actual_change < 0)
    if direction_correct:
        print(f"  Direction:       ✅ CORRECT")
    else:
        print(f"  Direction:       ❌ WRONG")
    
    print(f"\nResult: {result}")
    print(f"Assessment: {accuracy}")
    print("="*70)
    
    # Return validation data
    validation_data = {
        "prediction_time": prediction_time.isoformat(),
        "validation_time": validation_time.isoformat(),
        "wait_minutes": wait_minutes,
        "interval": interval,
        "predicted_price": float(predicted),
        "actual_price": float(actual_next_price),
        "current_price": float(current_price),
        "error_percent": error_percent,
        "expected_change_percent": expected_change,
        "actual_change_percent": actual_change,
        "direction_correct": direction_correct,
        "confidence": float(confidence),
        "result": result
    }
    
    return validation_data
    
    """

#new prediction function for signals
def live_direction_prediction(predictor, prices, volumes=None, interval='1h', wait_minutes=1):
    """
    Make a live direction prediction, wait for next candle, then validate
    
    Args:
        predictor: Trained PricePredictor
        prices: List of prices
        volumes: List of volumes (optional)
        interval: Candle interval
        wait_minutes: How long to wait for next candle
    
    Returns:
        dict with prediction results
    """
    print("\n" + "="*70)
    print(f"LIVE DIRECTION PREDICTION")
    print(f"Interval: {interval} | Wait time: {wait_minutes} minute(s)")
    print("="*70)
    
    # Make prediction
    direction, confidence = predictor.predict(prices, volumes)
    current_price = prices[-1]
    
    direction_str = "UP" if direction == 1 else "DOWN"
    
    prediction_time = datetime.now()
    
    print(f"\n[PREDICTION TIME] {prediction_time.strftime('%H:%M:%S')}")
    print(f"Current price:      ${current_price:.2f}")
    print(f"Predicted direction: {direction_str}")
    print(f"Confidence:         {confidence:.2%}")
    
    # Wait for next candle
    wait_seconds = wait_minutes * 60
    print(f"\n⏳ Waiting {wait_minutes} minute(s) for next candle to close...")
    print("-" * 70)
    
    # Countdown timer
    for i in range(wait_seconds, 0, -1):
        minutes_left = i // 60
        seconds_left = i % 60
        print(f"⏱️  {minutes_left:02d}:{seconds_left:02d} remaining...", end='\r')
        time.sleep(1)
    
    print("\n✓ Next candle has closed! Fetching new data...")
    
    # Fetch new data
    df = fetch_historical_data('BTCUSDT', days=1, interval=interval)
    
    if df is None:
        print("✗ Failed to fetch new data")
        return None
    
    new_prices = df['close'].tolist()
    actual_next_price = new_prices[-1]
    validation_time = datetime.now()
    
    # Calculate actual direction
    actual_change = ((actual_next_price - current_price) / current_price) * 100
    actual_direction = 1 if actual_change > 0 else 0
    
    # Check if direction was correct
    direction_correct = direction == actual_direction
    
    # Determine result
    if direction_correct:
        result = "✅ CORRECT"
    else:
        result = "❌ WRONG"
    
    # Display results
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    print(f"[VALIDATION TIME] {validation_time.strftime('%H:%M:%S')}")
    print(f"\nPrice Movement:")
    print(f"  Previous price: ${current_price:.2f}")
    print(f"  Current price:  ${actual_next_price:.2f}")
    print(f"  Change:         {actual_change:+.2f}%")
    print(f"\nDirection:")
    print(f"  Predicted:      {direction_str}")
    print(f"  Actual:         {'UP' if actual_direction == 1 else 'DOWN'}")
    print(f"  Result:         {result}")
    print(f"  Confidence:     {confidence:.2%}")
    print("="*70)
    
    # Return prediction data
    prediction_data = {
        "prediction_time": prediction_time.isoformat(),
        "validation_time": validation_time.isoformat(),
        "wait_minutes": wait_minutes,
        "interval": interval,
        "predicted_direction": int(direction),
        "predicted_direction_str": direction_str,
        "actual_direction": int(actual_direction),
        "actual_direction_str": "UP" if actual_direction == 1 else "DOWN",
        "current_price": float(current_price),
        "next_price": float(actual_next_price),
        "price_change_percent": actual_change,
        "direction_correct": int(direction_correct),
        "confidence": float(confidence),
        "result": result
    }
    
    return prediction_data

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TRADING BOT - LIVE PREDICTION VALIDATION")
    print("="*70)

    # ===== STEP 1: FETCH DATA =====
    print("\n[STEP 1] Fetching data...")
    df = fetch_historical_data('BTCUSDT', days=30, interval='1h')

    if df is None:
        print("✗ Failed to fetch data")
        exit(1)

    prices = df['close'].tolist()
    volumes = df['volume'].tolist()
    print(f"✓ Fetched {len(prices)} prices")
    print(f"  Price range: ${min(prices):.2f} - ${max(prices):.2f}")
    print(f"  Volume range: {min(volumes):.0f} - {max(volumes):.0f}")
    # Save prices
    save_prices_to_file(prices, volumes)

    # ===== STEP 2: TRAIN MODEL =====
    print("\n[STEP 2] Training model...")
    predictor = PricePredictor(lookback_period=24)
    success = predictor.train(prices, volumes)

    if not success:
        print("✗ Training failed")
        exit(1)

    print("✓ Training complete")

     # ===== STEP 3: MAKE PREDICTION =====  
    print("\n[STEP 3] Making prediction on latest data...")
    direction, confidence = predictor.predict(prices, volumes)
    
    if direction is not None:
        direction_str = "UP" if direction == 1 else "DOWN"
        print(f"✓ Predicted direction: {direction_str}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Current price: ${prices[-1]:.2f}")
    else:
        print("✗ Prediction failed")
        exit(1)

    # ===== STEP 4: SIMULATE PROFIT ===== 
    print("\n[STEP 4] Simulating profit on test data...")
    profit, equity = predictor.simulate_profit(prices, volumes)

    # ===== STEP 5: LIVE VALIDATION =====
    print("\n[STEP 5] Starting live validation...")
    result = live_direction_prediction(predictor, prices, interval='5m', wait_minutes=5)

    if result:
        save_validation_log(result)
        print("\n✓ Validation complete!")

    print("\n" + "="*70)
    print("DONE!")
    print("="*70)