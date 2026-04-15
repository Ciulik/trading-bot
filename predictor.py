import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, classification_report
from risk_manager import RiskManager
from trade_manager import TradeManager
class PricePredictor:
    def __init__(self, lookback_period=24):
        self.lookback_period = lookback_period
        self.is_trained = False
    
        # FIX: these must be strings, not variables
        self.feature_names = [
            "recent_momentum",
            "mean_return",
            "volatility",
            "ma_trend",
            "price_vs_ma",
            "price_momentum",
            "rsi",
            "vol_spike",
            "volume_pressure"
        ]
    
        self.model = RandomForestClassifier(
            n_estimators=450, #nr trees
            max_depth=5, #nr lyrs
            min_samples_leaf=40,
            min_samples_split=30,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1 #reproducible results 
        )

    def prepare_data(self, prices, volumes=None):
        X = []
        y = []

        # Loop through valid positions
        for i in range(len(prices) - self.lookback_period):
            # Get lookback_period prices as features
            window = np.array(prices[i: i + self.lookback_period])

            # feature 1 /returns
            returns = np.diff(window) / window[:-1]

            # feature 2 /recent momentum
            recent_momentum = returns[-1]

            # feature 3 / mean return (trend)
            mean_return = np.mean(returns)

            # feature 4 volatility
            volatility = np.std(returns)

            # feature 5 MA trend
            # short MA above long MA = uptrend
            short_ma = np.mean(window[-5:])
            long_ma = np.mean(window[-20:])
            ma_trend = short_ma - long_ma
            
            # feature 6 price vs MA
            price_vs_ma = (window[-1] - long_ma) / (long_ma + 1e-6)
            
            # feature 7 momentum /price diff
            price_momentum = window[-1] - window[0]

            # feature 8 RSI
            gains = [r for r in returns if r > 0]
            losses = [abs(r) for r in returns if r < 0]
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 1e-6
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # feature 9+10 if available
            if volumes is not None:
                vol_window = np.array(volumes[i:i + self.lookback_period])
                vol_mean = np.mean(vol_window[:-1])
                vol_spike = vol_window[-1] / (vol_mean + 1e-6)
                price_change = (window[-1] - window[-2]) / (window[-2] + 1e-6)
                volume_pressure = price_change * vol_spike
            else:
                vol_spike = 0
                volume_pressure = 0

            # BUILD FEATURE VECTORS
            features = [
                recent_momentum,
                mean_return,
                volatility,
                ma_trend,
                price_vs_ma,
                price_momentum,
                rsi,
                vol_spike,
                volume_pressure
            ]

            # LABEL

            horizon=10
            next_price = prices[i+self.lookback_period: i+self.lookback_period +horizon]
            current_price=window[-1]

            atr=volatility*current_price
            tp_price= current_price+(2*atr )
            sl_price= current_price -(1*atr)

            label=None
            
            for fp in next_price:
                if fp>=tp_price:
                 label=1 #tp hit good trade profittt
                 break
                elif fp <=sl_price:
                 label=0 #sl hit , lose oney
                 break

            if label is None:
                continue

            X.append(features)
            y.append(label)

        return np.array(X), np.array(y)

    def train(self, prices, volumes=None):
        X, y = self.prepare_data(prices, volumes)

        if len(X) < 10:
            print('Not enough data to train')
            return False
        
        # check class balance first
        up_pct = np.mean(y)
        print(f"Class balance → UP: {up_pct:.1%} | DOWN: {1-up_pct:.1%}")

        # split 80/20; no shuffle for time series
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # train
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        print(f"\nTrain accuracy: {accuracy_score(y_train, y_pred_train):.2%}")
        print(f"Test accuracy:  {accuracy_score(y_test, y_pred_test):.2%}")
        print(f"Test precision: {precision_score(y_test, y_pred_test):.2%}")
        
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred_test))
        
        # Feature importance
        print("Feature Importances:")
        importances = self.model.feature_importances_
        for name, imp in sorted(
            zip(self.feature_names, importances),
            key=lambda x: x[1],
            reverse=True
        ):
            bar = '||' * int(imp * 100)
            print(f"{name:<20} {imp:.4f} {bar}")

        return True 
    
    def predict(self, prices, volumes=None):
        if not self.is_trained:
            print("Model not trained!")
            return None, 0
        
        if len(prices) < self.lookback_period:
            print(f"Not enough data. Need {self.lookback_period}, got {len(prices)}")
            return None, 0
        
        window = np.array(prices[-self.lookback_period:])
        
        returns = np.diff(window) / window[:-1]
        recent_momentum = returns[-1]
        mean_return = np.mean(returns)
        volatility = np.std(returns)
        
        short_ma = np.mean(prices[-20:])
        long_ma = np.mean(prices[-50:])
        ma_trend = short_ma - long_ma
        
        price_vs_ma = (window[-1] - long_ma) / (long_ma + 1e-6)

        # FIX: scalar, not vector
        price_momentum = window[-1] - window[0]
        
        gains = [r for r in returns if r > 0]
        losses = [abs(r) for r in returns if r < 0]
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 1e-6
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        if volumes is not None:
            vol_window = np.array(volumes[-self.lookback_period:])
            vol_mean = np.mean(vol_window[:-1])
            vol_spike = vol_window[-1] / (vol_mean + 1e-6)
            price_change = (window[-1] - window[-2]) / (window[-2] + 1e-6)
            volume_pressure = price_change * vol_spike
        else:
            vol_spike = 0
            volume_pressure = 0
        
        features = np.array([[
            recent_momentum,
            mean_return,
            volatility,
            ma_trend,
            price_vs_ma,
            price_momentum,
            rsi,
            vol_spike,
            volume_pressure,
        ]])
        
        direction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        confidence = probabilities[direction]

        
        return direction, confidence

    def simulate_profit(self, prices, volumes=None, fee=0.001):
        """
        Simulate trading based on predictions
        fee = 0.001 means 0.1% per trade (Binance standard)
        """
        X, y = self.prepare_data(prices, volumes)

        # use last 20%
        if len(X) < 10:
            print("Not enough data to simulate")
            return None, None      
            
        split_idx = int(len(X) * 0.8)
        X_test = X[split_idx:]
        prices_test = prices[split_idx + self.lookback_period:]

        y_pred = self.model.predict(X_test)
        probs =self.model.predict_proba(X_test)
        size=RiskManager()
        
        profit = 0
        initial_balance=1000
        balance=initial_balance
        trades = 0
        wins = 0
        
        equity = []  # track equity curve
        tm=TradeManager(stop_loss_pct=2.0,take_profit_pct=2.0)

    
        for i in range(len(y_pred)):
          
            #check exits first before opening new trade
            current_price=prices_test[i]

            window=prices_test[max(0,i-50):i]

            if len(window)<50:
                continue

            short_ma=np.mean(window[-20:])
            long_ma=np.mea(window[-50:])

            trend=None

            if short_ma>long_ma:
                trend=1
            elif short_ma<long_ma:
                trend=0
            else:
                trend=None

            
            closed_trades=tm.check_exits(current_price)

            for trade in closed_trades:
                pnl=trade['pnl']
                fee_cost=abs(pnl) *fee
                net_pnl=pnl-fee_cost
                balance+=net_pnl
                trades+=1
                if pnl>0:
                    wins+=1


            if len(tm.active_trades)>=3:
                equity.append(balance)
                continue

            direction=y_pred[i]
            confidence=probs[i][direction]

            if trend is None:
                continue
                #this is to trade only on hte same direction with the trend, either up or down
            if direction!=trend:
                continue


            if confidence<0.55:
                equity.append(balance)
                continue

            position=size.position_size(confidence,balance)

            if position ==0:
                equity.append(balance)
                continue

        
            tm.open_trade(current_price, direction,position,confidence )





            equity.append(balance)

        win_rate = wins / trades if trades > 0 else 0 



        total_return= (balance-initial_balance)/initial_balance

        print(f"\n{'='*40}")
        print(f"PROFIT SIMULATION RESULTS")
        print(f"{'='*40}")
        print(f"Total trades:   {trades}")
        print(f"Win rate:       {win_rate:.2%}")
        print(f"balance{balance:.2%}")
        print(f"Total return:   {total_return:.2%}")
        print(f"Avg per trade:  {total_return/trades:.4%}" if trades > 0 else 0 )
        
        # max drawdown
        peak = initial_balance
        max_dd = 0
        
        for e in equity:
            peak = max(peak, e)
            drawdown = (peak - e) /peak
            max_dd = max(max_dd, drawdown)
            
        print(f"Max drawdown:   {max_dd:.2%}")
        print(f"{'='*40}")
        
        return profit, equity

if __name__ == "__main__":
    print("="*70)
    print("TESTING DirectionPredictor - Day 2")
    print("="*70)
    
    # Sample data
    sample_prices = [100, 102, 101, 105, 103, 108, 106, 110, 109, 115, 
                     113, 120, 118, 125, 123, 130, 128, 135, 133, 140,
                     138, 145, 143, 150, 148, 155, 153, 160, 158, 165]
    
    # Create and train
    predictor = PricePredictor(lookback_period=5)
    success = predictor.train(sample_prices)
    
    if success:
        print("\n" + "="*70)
        print("MAKING PREDICTIONS")
        print("="*70)
        
        direction, confidence = predictor.predict(sample_prices)
        
        if direction is not None:
            direction_str = "UP" if direction == 1 else "DOWN"
            print(f"\nPredicted direction: {direction_str}")
            print(f"Confidence: {confidence:.2%}")
        
        print("\n" + "="*70)
        print("SIMULATING PROFIT")
        print("="*70)
        
        profit, equity = predictor.simulate_profit(sample_prices)