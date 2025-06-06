import typer
from cli.analysis_helper import analysis_command
from cli.backtest_helper import backtest_command
from constants import END_DT, START_DT
from data.api.polygon import PolygonAPI
from data.options.fetch_0dte import Fetch0DTE

app = typer.Typer()


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
    analysis_command(symbol)


if __name__ == "__main__":
    app()
