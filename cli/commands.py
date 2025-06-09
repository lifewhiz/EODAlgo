import typer
from cli.analysis_helper import analysis_command
from cli.backtest_helper import backtest_command
from constants import END_DT, START_DT
from data.api.polygon import PolygonAPI
from data.options.fetch_0dte import Fetch0DTE
from data.options.synthetic_0dte import SyntheticDataGenerator

app = typer.Typer()


def data_command(symbol):
    print(f"Pulling data for {symbol} from {START_DT} to {END_DT}")
    api = PolygonAPI()
    fetcher = Fetch0DTE(api, api, START_DT, END_DT)
    contracts = fetcher.fetch_0dte_bars_agg("SPX")
    print(f"Fetched {len(contracts)} contracts for {symbol}")

def synthetic_data_command(symbol):
    print(f"Pulling synthetic data for {symbol} from {START_DT} to {END_DT}")
    gen = SyntheticDataGenerator()
    contracts = gen.generate_synthetic_data("SPX")
    print(f"Fetched {len(contracts)} synthetic contracts for {symbol}")

def synthetic_clean_command(symbol):
    print(f"Cleaning synthetic data for {symbol}")
    gen = SyntheticDataGenerator()
    gen.clean_synthetic_data("SPX")


@app.command()
def backtest(symbol: str = "SPX", strategy_name: str = "Expiration"):
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
def synthetic_clean(symbol: str = "SPX"):
    """
    Cleans the synthetic data for the specified symbol.
    """
    synthetic_clean_command(symbol)

@app.command()
def synthetic_data(symbol: str = "SPX"):
    """
    Fetches the 0DTE data for the specified symbol.
    """
    synthetic_data_command(symbol)


@app.command()
def analysis(symbol: str = "SPX"):
    """
    Runs EOD activation/movement/expiry gain analysis for a given symbol.
    """
    analysis_command(symbol)


if __name__ == "__main__":
    app()
