# 📈 Algorithmic Trading Bot & Market Predictor

## 📌 Overview
An end-to-end machine learning system designed to predict market trends and automate trading execution. The system leverages tree-based algorithms and real-time API data ingestion to backtest strategies and simulate live environments.

## ⚙️ Features
- **Data Ingestion:** Real-time data fetching via external financial APIs.
- **Predictive Modeling:** Utilizes Decision Trees and Random Forests to classify market movements and predict price vectors.
- **Backtesting Engine:** Custom framework to simulate trading strategies against historical data, optimizing for risk control and maximum drawdown.
- **Model Evaluation:** Implements k-fold cross-validation and hyperparameter tuning to ensure robust generalization across volatile market conditions.

## 🚀 Tech Stack
- **Languages:** Python
- **Machine Learning:** scikit-learn, pandas, numpy
- **Integration:** REST APIs, JSON parsing

## 🛠️ How to Run Locally
To simulate historical backtests or initiate live market predictions:
1. **Clone and Navigate:** `git clone https://github.com/Ciulik/trading-bot.git && cd trading-bot`
2. **Install Dependencies:** `pip install -r requirements.txt`
3. **Environment Setup:** Create a `.env` file in the root directory and add your broker/market credentials (e.g., `MARKET_API_KEY=your_key_here`).
4. **Execute Pipeline:**
   - Historical Backtest: `python backtest.py`
   - Live Prediction: `python live_prediction.py`
