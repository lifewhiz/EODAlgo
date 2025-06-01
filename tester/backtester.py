from datetime import date, timedelta
from typing import List

import pandas as pd
import pandas_market_calendars as mcal
from pandera.typing import DataFrame
from tqdm import tqdm

from data.models import Contract
from strategy.base_strategy import MARKET_CLOSE, BaseStrategy
from tester.models import CandleModel
from tester.data_handler import DataHandler


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
            self._process_day_minute_by_minute(contract, current_date, stock_candles)

    def _process_day_minute_by_minute(
        self,
        contract: Contract,
        current_date: date,
        stock_candles: DataFrame[CandleModel],
    ):
        option_df: DataFrame[CandleModel] = self.data.get_option_candles(
            contract.symbol
        )
        entry_df = option_df[option_df["date"] == current_date]

        if entry_df.empty:
            print(f"⚠️ Warning: No data for {contract.symbol} on {current_date}")
            return

        for i in range(len(entry_df)):
            op_slice = entry_df.iloc[: i + 1]
            stock_slice = stock_candles.iloc[: i + 1]

            if not self.strategy.entry(contract, op_slice, stock_slice):
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
        buy_price = self.strategy.compute_mid_price(entry_op_candle)
        minute: pd.Timestamp = entry_op_candle.timestamp

        exit_df: DataFrame[CandleModel] = self.data.get_option_candles(contract.symbol)
        exit_df = exit_df[exit_df["date"] == current_date]
        exit_df["time"] = exit_df["timestamp"].dt.time

        end_time = minute.replace(hour=20, minute=0)

        while minute <= end_time:
            exit_op_candles = exit_df[exit_df["time"] <= minute.time()]
            exit_stock_candles = stock_candles[stock_candles["timestamp"] <= minute]

            if self.strategy.exit_condition_met(
                contract=contract,
                current_date=current_date,
                option_candles=exit_op_candles,
                stock_candles=exit_stock_candles,
                buy_price=buy_price,
            ):
                return
            minute += timedelta(minutes=1)

        # Final fallback exit
        final_exit_df = exit_df[exit_df["time"] <= MARKET_CLOSE]
        final_exit_stock_df = stock_candles[
            stock_candles["timestamp"].dt.time <= MARKET_CLOSE
        ]

        assert (
            final_exit_df.iloc[-1].time == MARKET_CLOSE
        ), f"Expected last candle to be market close for {contract.symbol}."
        assert self.strategy.exit_condition_met(
            contract=contract,
            current_date=current_date,
            candles=final_exit_df,
            stock_candles=final_exit_stock_df,
            buy_price=buy_price,
        ), f"Strategy did not exit by EOD for {contract.symbol}."
