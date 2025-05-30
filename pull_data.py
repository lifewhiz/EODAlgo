from datetime import datetime
from api.polygon import PolygonAPI
from api.yahoo import YahooAPI
from data.options.fetch_0dte import Fetch0DTE
from data.options.process_0dte import load_contracts_from_json

START_DT = "2025-05-01"
END_DT = "2025-05-24"


options_api = PolygonAPI()
stocks_api = YahooAPI()
fetcher = Fetch0DTE(options_api, stocks_api, START_DT, END_DT)
contracts = fetcher.fetch_0dte_bars_agg("SPX")
