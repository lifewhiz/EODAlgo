from constants import END_DT, START_DT
from strategy.exp_strategy import ExpStrategy
from tester.backtester import Backtester


def backtest_command(symbol: str, strategy_name: str):
    if strategy_name == "Expiration":
        strategy = ExpStrategy(symbol=symbol)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    backtester = Backtester(strategy)
    portfolio = backtester.run(start_date=START_DT, end_date=END_DT)
    portfolio.summary()
