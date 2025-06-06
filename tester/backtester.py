from datetime import date, timedelta
from typing import List

import pandas as pd
import pandas_market_calendars as mcal
from pandera.typing import DataFrame
from tqdm import tqdm

from data.models import Contract
from constants import MARKET_CLOSE
from strategy.base_strategy import BaseStrategy
from tester.models import CandleModel
from data.data_handler import DataHandler


class Backtester:
    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.data = DataHandler(strategy.symbol)

    def _get_trading_days(self, start: date, end: date) -> List[date]:
        calendar = mcal.get_calendar("NYSE")
        return [
            dt.date()
            for dt in calendar.valid_days(
                start_date=str(start), end_date=str(end)
            ).to_pydatetime()
        ]

    def run(self, start_date: date, end_date: date):
        for current_date in tqdm(
            self._get_trading_days(start_date, end_date), desc="Processing Days"
        ):
            self._process_day(current_date)
        return self.strategy.portfolio

    def _process_day(self, current_date: date):
        daily_contracts = self.data.get_contracts_for_date(current_date)
        stock_candles = self.data.get_stock_candles(current_date)

        for contract in daily_contracts:
            self._process_day_minutely(contract, stock_candles)

    def _process_day_minutely(
        self,
        contract: Contract,
        stock_candles: DataFrame[CandleModel],
    ):
        option_candles: DataFrame[CandleModel] = self.data.get_option_candles(
            contract.symbol
        )

        for i in range(len(option_candles)):
            op_slice = option_candles.iloc[: i + 1]
            stock_slice = stock_candles.iloc[: i + 1]

            if not self.strategy.entry_wrapper(contract, op_slice, stock_slice):
                continue

            self._process_contract(contract, option_candles, stock_candles)
            break  # Only one entry per contract per day

    def _process_contract(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ):
        cur_time: pd.Timestamp = option_candles.iloc[0].timestamp
        end_time = cur_time.replace(hour=20, minute=0)

        while cur_time <= end_time:
            exit_op_candles = option_candles[option_candles["timestamp"] <= cur_time]
            exit_stock_candles = stock_candles[stock_candles["timestamp"] <= cur_time]

            if self.strategy.exit_wrapper(
                contract=contract,
                option_candles=exit_op_candles,
                stock_candles=exit_stock_candles,
            ):
                return

            cur_time += timedelta(minutes=1)

        # Final fallback exit (end of day)
        assert self.strategy.exit_wrapper(
            contract=contract,
            option_candles=option_candles,
            stock_candles=stock_candles,
        ), f"Strategy did not exit by EOD for {contract.symbol}."
