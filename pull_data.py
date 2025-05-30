from data.api.polygon import PolygonAPI
from data.options.fetch_0dte import Fetch0DTE

START_DT = "2025-01-01"
END_DT = "2025-05-30"


api = PolygonAPI()
fetcher = Fetch0DTE(api, api, START_DT, END_DT)
contracts = fetcher.fetch_0dte_bars_agg("SPX")
