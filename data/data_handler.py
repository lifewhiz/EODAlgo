from collections import defaultdict
from datetime import date, time, datetime, timezone
from typing import List, Dict

import pandas as pd
from pandera.typing import DataFrame

from data.funcs import get_stock_symbol
from data.models import Candle, Contract
from data.options.process_0dte import load_contracts_from_json
from data.stocks.process_stocks import load_stock_from_json
from constants import MARKET_OPEN, MARKET_CLOSE
from tester.models import CandleModel


class DataHandler:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.contracts_by_date: Dict[str, List[Contract]] = (
            self._index_contracts_by_date(load_contracts_from_json(symbol))
        )
        self.option_candles_by_symbol = self._index_option_candles()
        self.stock_candles_dt_df: Dict[str, DataFrame[CandleModel]] = (
            self._index_stock_candles()
        )

    def parse_dt(self, dt: date) -> str:
        return dt.strftime("%Y-%m-%d")

    def _get_tz_aware_datetime(self, dt: date, tm: time) -> datetime:
        return datetime.combine(dt, tm, tzinfo=timezone.utc)

    def _load_and_validate_stock_data(self) -> DataFrame[CandleModel]:
        raw_candles: List[Candle] = load_stock_from_json(get_stock_symbol(self.symbol))
        return self._prepare_candle_df(raw_candles)

    def _index_contracts_by_date(
        self, contracts: List[Contract]
    ) -> Dict[str, List[Contract]]:
        contracts_by_date = defaultdict(list)
        for c in contracts:
            expiry = self.parse_dt(c.expiry.date())
            contracts_by_date[expiry].append(c)
        return contracts_by_date

    def _index_option_candles(self) -> Dict[str, DataFrame[CandleModel]]:
        option_candles_by_symbol: Dict[str, List[Candle]] = dict()

        for contract_list in self.contracts_by_date.values():
            for c in contract_list:
                option_candles_by_symbol[c.symbol] = c.data

        return {
            symbol: self._prepare_candle_df(candles)
            for symbol, candles in option_candles_by_symbol.items()
        }

    def _index_stock_candles(self) -> Dict[str, DataFrame[CandleModel]]:
        stock_candles = self._load_and_validate_stock_data()
        return {self.parse_dt(dt): df for dt, df in stock_candles.groupby("date")}

    def _prepare_candle_df(self, candles: List[Candle]) -> DataFrame[CandleModel]:
        if MARKET_CLOSE not in {c.timestamp.time() for c in candles}:
            candles.append(
                Candle(
                    open=candles[-1].open,
                    high=candles[-1].high,
                    low=candles[-1].low,
                    close=candles[-1].close,
                    volume=candles[-1].volume,
                    vwap=candles[-1].vwap,
                    timestamp=self._get_tz_aware_datetime(
                        candles[-1].timestamp.date(), MARKET_CLOSE
                    ),
                )
            )

        df = pd.DataFrame([vars(c) for c in candles])
        df = df.sort_values("timestamp")
        df["date"] = df["timestamp"].dt.date
        CandleModel.validate(df)
        return df

    def get_contracts_for_date(self, dt: date) -> List[Contract]:
        return self.contracts_by_date.get(self.parse_dt(dt), [])

    def get_option_candles(self, symbol: str) -> DataFrame[CandleModel]:
        return self.process_candles(self.option_candles_by_symbol[symbol])

    def get_stock_candles(self, dt: date) -> DataFrame[CandleModel]:
        return self.process_candles(self.stock_candles_dt_df[self.parse_dt(dt)])

    def process_candles(
        self, candles: DataFrame[CandleModel]
    ) -> DataFrame[CandleModel]:
        candles = candles[
            (candles["timestamp"].dt.time <= MARKET_CLOSE)
            & (candles["timestamp"].dt.time >= MARKET_OPEN)
        ]
        candles = candles.set_index("timestamp", drop=False)
        dt = candles["date"].iloc[-1]
        candles = candles.reindex(
            pd.date_range(
                start=self._get_tz_aware_datetime(dt, MARKET_OPEN),
                end=self._get_tz_aware_datetime(dt, MARKET_CLOSE),
                freq="1min",
            ),
            method="bfill",
        )
        assert candles[candles["close"].isna()].empty, "Missing data in candles"
        return candles
