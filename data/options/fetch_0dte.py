from datetime import datetime, timedelta
import math
from typing import Dict, List
from api.base import BaseAPI
from data.options.process_0dte import load_contracts_from_json, save_contracts_as_json
from data.stocks.process_stocks import ProcessStocks
from models import Candle, Contract, ContractType
import pandas_market_calendars as mcal
import time

INDEX_DT = {
    "SPX": {
        "option_symbol": "SPXW",
        "stock_symbol": "^SPX",
    }
}


class Fetch0DTE:
    """
    Fetches 0DTE (Zero Days to Expiration) option contracts for a given symbol.
    """

    def __init__(
        self, options_api: BaseAPI, stocks_api: BaseAPI, start_dt: str, end_dt: str
    ):
        self.options_api = options_api
        self.stocks_process = ProcessStocks(stocks_api)

        self.open_market_days = set(
            list(
                self.parse_dt(dt)
                for dt in mcal.get_calendar("NYSE")
                .valid_days(start_date=start_dt, end_date=end_dt)
                .to_pydatetime()
            )
        )
        if not self.open_market_days:
            raise ValueError("No open market days found in the specified range.")
        self.start_dt = self.parse_dt_str(start_dt)
        self.end_dt = self.parse_dt_str(end_dt)

        self.def_wait_time = 60  # Default wait time in seconds for API calls
        self.def_eod_timeframe = 30  # last 30 minutes of the day
        self.def_eod_wait_time = 5  # 5 minutes after timeframe

        self.existing_contracts = dict()

    def set_existing_contracts(self, symbol: str):
        contracts = load_contracts_from_json(self.get_option_symbol(symbol))
        self.existing_contracts = {contract.symbol: contract for contract in contracts}

    def parse_dt_str(self, dt_str: str) -> datetime:
        """
        Parses a date string in 'YYYY-MM-DD' format into a datetime object.

        :param dt_str: Date string to parse.
        :return: Parsed datetime object.
        """
        return datetime.strptime(dt_str, "%Y-%m-%d")

    def parse_dt(self, dt: datetime) -> str:
        """
        Converts a datetime object to a string in 'YYYY-MM-DD' format.

        :param dt: Datetime object to convert.
        :return: Formatted date string.
        """
        return dt.strftime("%Y-%m-%d")

    def api_fetch_retry(self, func, *args, **kwargs):
        """
        Retry mechanism for API calls to handle transient errors.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(self.def_wait_time)
                if attempt < max_retries - 1:
                    continue
                else:
                    print("Max retries reached. Returning empty list.")
                    return []

    def get_option_symbol(self, symbol: str) -> str:
        return INDEX_DT[symbol]["option_symbol"] if symbol in INDEX_DT else symbol

    def get_stock_symbol(self, symbol: str) -> str:
        return INDEX_DT[symbol]["stock_symbol"] if symbol in INDEX_DT else symbol

    def fetch_0dte_strikes(
        self,
        stock_candles: List[Candle],
        dt: datetime,
    ) -> Dict[ContractType, List[float]]:
        filtered_candles = [
            candle for candle in stock_candles if candle.timestamp.date() == dt.date()
        ]
        eod_candles = filtered_candles[-self.def_eod_timeframe :]
        eod_fst_candles = eod_candles[: self.def_eod_wait_time]

        low, high = (
            min(candle.low for candle in eod_fst_candles),
            max(candle.high for candle in eod_fst_candles),
        )

        def truncate_float(n, places):
            factor = 10**places
            return int(n * factor) / factor

        def ceil_float(n, places):
            factor = 10**places
            return math.ceil(n * factor) / factor

        low = truncate_float(low, -1)
        high = ceil_float(high, -1)

        return {
            ContractType.CALL: [high],
            ContractType.PUT: [low],
        }

    def fetch_0dte_bars(
        self,
        symbol: str,
        contract_strike: float,
        contract_type: ContractType,
        dt: datetime,
    ) -> Contract:
        contract_symbol = self.options_api.format_occ_option_symbol(
            self.get_option_symbol(symbol), dt, contract_type, contract_strike
        )

        if contract_symbol in self.existing_contracts:
            contract = self.existing_contracts[contract_symbol]
        else:
            candles = self.api_fetch_retry(
                self.options_api.get_option_contract_candles,
                contract_symbol,
                dt,
                dt,
            )
            contract = Contract(
                symbol=contract_symbol,
                underlying_symbol=self.get_stock_symbol(symbol),
                expiry=dt,
                strike=contract_strike,
                contract_type=contract_type,
                data=candles,
            )

        return contract

    def fetch_0dte_bars_agg(self, symbol: str) -> List[Contract]:
        """
        Fetches historical candle data for a specific option contract.

        :param contract_symbol: The symbol of the option contract.
        :return: List of Candle objects containing historical data.
        """
        contracts = []
        contract_types = [ContractType.CALL, ContractType.PUT]
        cur_dt = self.start_dt

        stock_candles = self.stocks_process.fetch_stocks(
            symbol=self.get_stock_symbol(symbol),
            from_dt=self.start_dt,
            to_dt=self.end_dt,
        )
        self.set_existing_contracts(symbol)

        while cur_dt <= self.end_dt:
            if self.parse_dt(cur_dt) in self.open_market_days:
                contract_strikes = self.fetch_0dte_strikes(stock_candles, cur_dt)
                for contract_type in contract_types:
                    for strike in contract_strikes[contract_type]:
                        contracts.append(
                            self.fetch_0dte_bars(
                                symbol,
                                strike,
                                contract_type,
                                cur_dt,
                            )
                        )
                        time.sleep(10) # Sleep to avoid hitting API rate limits
            cur_dt += timedelta(days=1)

        save_contracts_as_json(contracts)
        return contracts
