# EODAlgo

A modular framework for simulating 0DTE (zero-days-to-expiry) options strategies using real intraday data.

## 📁 Directory Structure

```graphql
├── analysis/                 # Data visualization and insights
│   ├── activation.py         # Activation time analysis
│   ├── direction.py          # Directional move analysis
│   └── expiry.py             # Expiry gain visualization
├── artifacts/                # Saved figures and visual output
│   ├── activation_times.png
│   ├── direction_clusters.png
│   └── expiry_gains.png
├── cli/                      # CLI commands for running the app
│   ├── analysis_helper.py
│   ├── backtest_helper.py
│   ├── commands.py
│   └── __init__.py
├── constants.py              # Global date range and shared constants
├── data/                     # Data-related modules
│   ├── api/                  # Interfaces to external APIs
│   ├── data_handler.py       # Unified stock/options loading
│   ├── funcs.py              # Shared helpers
│   ├── models.py             # Shared data types (Contract, Candle, etc.)
│   ├── options/              # 0DTE options processing (real + synthetic)
│   ├── stocks/               # Stock data cleaning & prep
│   └── storage/              # Local JSON cache
├── main.py                   # Entry point for CLI (Typer)
├── ml/                       # ML-specific modules (WIP)
├── portfolio/                # Portfolio tracking
│   ├── models.py
│   └── portfolio.py
├── requirements.txt          # Python dependencies
├── requirements_rl.txt       # RL-specific dependencies
├── strategy/                 # Strategy definitions
│   ├── base_strategy.py      # Abstract base class
│   ├── exp_strategy.py       # EOD reversal strategy logic
│   └── __init__.py
└── tester/                   # Backtesting engine
    ├── backtester.py
    ├── __init__.py
    └── models.py
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

### 🧰 Synthetic Data Generation

```bash
python main.py synthetic-data --symbol SPX
```

- Generate synthetic options around the open/close price for each day.
- Include both calls and puts, spaced every 5 points across ±50pt from reference price.

### 🧪 Run a Strategy Backtest

```bash
python main.py backtest --symbol SPX --strategy-name Expiration
```

### 📊 Generate Analysis Visuals

```bash
python main.py analysis --symbol SPX
```

### 📈 Strategies

To create a custom strategy, inherit from `BaseStrategy` and implement the following methods:

```python
entry(
    self,
    option_map: Dict[Contract, DataFrame[CandleModel]],
    stock_candles: DataFrame[CandleModel]
) -> Optional[Contract]
```

Return a `Contract` to enter a trade, or `None` to skip.

```python
exit(
    self,
    contract: Contract,
    option_candles: DataFrame[CandleModel],
    stock_candles: DataFrame[CandleModel]
) -> bool
```

Return `True` to exit the trade, `False` to continue holding.
