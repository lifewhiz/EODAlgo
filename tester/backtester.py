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
            self._process_day_minutely(contract, current_date, stock_candles)

    def _process_day_minutely(
        self,
        contract: Contract,
        current_date: date,
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

            entry_op_candle = op_slice.iloc[-1]
            self._process_contract(
                contract, current_date, entry_op_candle, stock_candles
            )
            break  # Only one entry per contract per day

    def _process_contract(
        self,
        contract: Contract,
        current_date: date,
        entry_op_candle: CandleModel,
        stock_candles: DataFrame[CandleModel],
    ):
        minute: pd.Timestamp = entry_op_candle.timestamp

        option_candles: DataFrame[CandleModel] = self.data.get_option_candles(
            contract.symbol
        )
        option_candles = option_candles[option_candles["date"] == current_date]
        option_candles["time"] = option_candles["timestamp"].dt.time

        end_time = minute.replace(hour=20, minute=0)

        while minute <= end_time:
            exit_op_candles = option_candles[option_candles["time"] <= minute.time()]
            exit_stock_candles = stock_candles[stock_candles["timestamp"] <= minute]

            if self.strategy.exit_wrapper(
                contract=contract,
                option_candles=exit_op_candles,
                stock_candles=exit_stock_candles,
            ):
                return

            minute += timedelta(minutes=1)

        # Final fallback exit (end of day)
        final_option_candles = option_candles[option_candles["time"] <= MARKET_CLOSE]
        final_stock_candles = stock_candles[
            stock_candles["timestamp"].dt.time <= MARKET_CLOSE
        ]

        assert (
            final_option_candles.iloc[-1].time == MARKET_CLOSE
        ), f"Expected last candle to be market close for {contract.symbol}."
        assert self.strategy.exit_wrapper(
            contract=contract,
            option_candles=final_option_candles,
            stock_candles=final_stock_candles,
        ), f"Strategy did not exit by EOD for {contract.symbol}."
