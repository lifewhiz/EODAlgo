# EODAlgo

A modular framework for simulating 0DTE (zero-days-to-expiry) options strategies using real intraday data.

## 📁 Directory Structure

```graphql
├── cli/                      # CLI commands for running the app
│   └── commands.py
├── constants.py              # Global date range and shared constants
├── data/                     # Data-related modules
│   ├── api/                  # Interfaces to external APIs (Polygon, Yahoo, Mock)
│   ├── funcs.py              # Shared data helpers
│   ├── models.py             # Shared data models (Candle, Contract, etc.)
│   ├── options/              # 0DTE options data processing
│   ├── stocks/               # Stock price data processing
│   └── storage/              # Local JSON cache of pulled data
│       ├── options/
│       └── stocks/
├── main.py                   # Entry point for CLI (typer-based)
├── portfolio/                # Portfolio and PnL tracking
│   ├── models.py
│   └── portfolio.py
├── requirements.txt          # Python dependencies
├── strategy/                 # Strategy implementations
│   ├── base_strategy.py
│   └── puts_exp_strategy.py
├── tester/                   # Backtesting engine
│   ├── backtester.py
│   ├── data_handler.py
│   └── models.py
└── README.md
```

## 🚀 Setup

```bash
python -m venv venv
source venv/bin/activate        # On UNIX/macOS
# venv\Scripts\activate.bat     # On Windows
pip install -r requirements.txt
```

### 🔑 API Key Setup

If using Polygon.io for data, set your API key as an environment variable:

```bash
export POLYGON_API_KEY=your_key_here     # UNIX/macOS
# setx POLYGON_API_KEY your_key_here     # Windows
```

### 📅 Modify Date Range

In `constants.py`, set the date range:

```python
START_DT = date(2025, 1, 1)
END_DT = date(2025, 5, 30)
```

### 📦 Fetch 0DTE Option + Stock Data

```bash
python main.py data --symbol SPX
```

### 🧪 Run a Strategy Backtest

```bash
python main.py backtest --symbol SPX --strategy-name PutsExpiration
```

### 📈 Strategies

To create a custom strategy, inherit from `BaseStrategy` and implement the following methods:

```python
entry(self, contract: Contract, option_candles: DataFrame[CandleModel], stock_candles: DataFrame[CandleModel]) -> bool
```

```python
exit(self, contract: Contract, option_candles: DataFrame[CandleModel], stock_candles: DataFrame[CandleModel]) -> bool
```
