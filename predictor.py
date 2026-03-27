import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class PricePredictor:
    def __init__(self, lookback_period=24):
        """
        Initialize the price predictor
        
        Args:
            lookback_period: Number of hours/candles to use for prediction
        """
        self.lookback_period = lookback_period
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_data(self, prices):
        """
        Convert prices to X, y format for training
        
        Args:
            prices: List of prices
        
        Returns:
            tuple: (X, y) numpy arrays
        """
        self.prices = prices
        X = []
        y = []

        # Loop through valid positions
        for i in range(len(prices) - self.lookback_period):
            # Get lookback_period prices as features
            X_window = prices[i : i + self.lookback_period]
            X.append(X_window)

            # Get the next price as target
            y_value = prices[i + self.lookback_period]
            y.append(y_value)

        return np.array(X), np.array(y)

    def train(self, prices):
        """
        Train the model on historical prices
        
        Args:
            prices: List of historical prices
        
        Returns:
            bool: True if training succeeded, False otherwise
        """
        # Check if we have enough data
        if not prices or len(prices) < self.lookback_period + 1:
            print(f"Not enough data. Need at least {self.lookback_period + 1} prices, got {len(prices)}")
            return False

        # Get X, y from prepare_data
        X, y = self.prepare_data(prices)

        if len(X) < 2:
            print("Not enough data to train")
            return False

        # Normalize X using StandardScaler
        X_scaled = self.scaler.fit_transform(X)

        # Train the model
        self.model.fit(X_scaled, y)

        # Set the flag
        self.is_trained = True

        # Calculate R² score (confidence)
        score = self.model.score(X_scaled, y)
        print(f"Model trained! R² score: {score:.4f}")

        return True

    def predict(self, prices):
        """
        Predict the next price
        
        Args:
            prices: List of recent prices
        
        Returns:
            tuple: (predicted_price, confidence_score)
        """
        # Check if model is trained
        if not self.is_trained:
            print("Model not trained!")
            return None, 0

        # Check if we have enough data
        if len(prices) < self.lookback_period:
            print(f"Not enough data for prediction. Need {self.lookback_period} prices, got {len(prices)}")
            return None, 0

        # Get the last lookback_period prices
        recent_prices = prices[-self.lookback_period:]

        # Reshape to 2D array (1 sample, lookback_period features)
        recent_array = np.array([recent_prices])

        # Normalize using the learned scaler
        recent_scaled = self.scaler.transform(recent_array)

        # Make prediction
        predicted_array = self.model.predict(recent_scaled)
        predicted_price = predicted_array  # Extract scalar value

        # Calculate confidence on training data
        X, y = self.prepare_data(prices)
        X_scaled = self.scaler.transform(X)
        confidence = self.model.score(X_scaled, y)

        return predicted_price, confidence


if __name__ == "__main__":
    # Test with sample data
    predictor = PricePredictor(lookback_period=3)
    sample_prices = [100, 105, 110, 115, 120, 125, 130, 135, 140, 145]

    # Train
    predictor.train(sample_prices)

    # Predict
    predicted, confidence = predictor.predict(sample_prices)

    print(f"Predicted price: ${predicted:.2f}")
    print(f"Confidence: {confidence:.2%}")