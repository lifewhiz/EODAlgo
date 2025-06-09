from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import pandas_market_calendars as mcal
from pandera.typing import DataFrame
from tqdm import tqdm

from data.models import Contract
from strategy.base_strategy import BaseStrategy
from tester.models import CandleModel
from data.data_handler import DataHandler


class Backtester:
    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.data = DataHandler(strategy.symbol, include_synthetic=True)

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
        contracts = self.data.get_contracts_for_date(current_date)
        stock_candles = self.data.get_stock_candles(current_date)

        option_map: Dict[Contract, DataFrame[CandleModel]] = {
            contract: self.data.get_option_candles(contract.symbol)
            for contract in contracts
        }

        for i in range(len(stock_candles)):
            stock_slice = stock_candles.iloc[: i + 1]
            sliced_option_map = {
                c: candles.iloc[: i + 1] for c, candles in option_map.items()
            }

            selected_contract: Optional[Contract] = self.strategy.entry_wrapper(
                contracts_to_candles=sliced_option_map,
                stock_candles=stock_slice,
            )

            if selected_contract is not None:
                self._process_contract(
                    stock_slice.iloc[-1].timestamp + timedelta(minutes=1),
                    selected_contract,
                    option_map[selected_contract],
                    stock_candles,
                )
                break

    def _process_contract(
        self,
        cur_time: datetime,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ):
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
