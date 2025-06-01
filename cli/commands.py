from datetime import date
import typer
from cli.analysis_commands import metric_analysis
from constants import END_DT, START_DT
from data.api.polygon import PolygonAPI
from data.options.fetch_0dte import Fetch0DTE
from strategy.puts_exp_strategy import PutsExpirationStrategy
from tester.backtester import Backtester

app = typer.Typer()


def backtest_command(symbol: str, strategy_name: str):
    if strategy_name == "PutsExpiration":
        strategy = PutsExpirationStrategy(symbol=symbol)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    backtester = Backtester(strategy)
    portfolio = backtester.run(start_date=START_DT, end_date=END_DT)
    portfolio.summary()


def data_command(symbol):
    print(f"Pulling data for {symbol} from {START_DT} to {END_DT}")
    api = PolygonAPI()
    fetcher = Fetch0DTE(api, api, START_DT, END_DT)
    contracts = fetcher.fetch_0dte_bars_agg("SPX")
    print(f"Fetched {len(contracts)} contracts for {symbol}")


@app.command()
def backtest(symbol: str = "SPX", strategy_name: str = "PutsExpiration"):
    """
    Runs the backtest for the specified strategy and symbol.
    """
    backtest_command(symbol, strategy_name)


@app.command()
def data(symbol: str = "SPX"):
    """
    Fetches the 0DTE data for the specified symbol.
    """
    data_command(symbol)


@app.command()
def analysis(symbol: str = "SPX"):
    """
    Runs EOD activation/movement/expiry gain analysis for a given symbol.
    """
    metric_analysis(symbol)


if __name__ == "__main__":
    app()
