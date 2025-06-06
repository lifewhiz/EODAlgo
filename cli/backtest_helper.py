from constants import END_DT, START_DT
from strategy.puts_exp_strategy import PutsExpirationStrategy
from strategy.sma_rsi_strategy import SmaRsiStrategy
from tester.backtester import Backtester


def backtest_command(symbol: str, strategy_name: str):
    if strategy_name == "PutsExpiration":
        strategy = PutsExpirationStrategy(symbol=symbol)
    elif strategy_name == "SmaRsi":
        strategy = SmaRsiStrategy(symbol=symbol)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    backtester = Backtester(strategy)
    portfolio = backtester.run(start_date=START_DT, end_date=END_DT)
    portfolio.summary()
