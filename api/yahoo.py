from datetime import datetime, timedelta
from typing import List

import pandas as pd
from api.base import BaseAPI
from models import Candle
import yfinance as yf


class YahooAPI(BaseAPI):
    """
    Yahoo Finance API implementation for fetching option contract candles.
    """

    def __init__(self):
        super().__init__()

    def get_option_contract_candles(
        self, contract_symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        raise NotImplementedError(
            "Yahoo Finance API does not support fetching option contract candles directly."
        )

    def get_stock_candles(
        self, symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        """
        Fetches historical candle data for a specific stock from Yahoo Finance.

        :param symbol: The stock symbol (e.g., "AAPL").
        :param from_dt: Start date for fetching candles.
        :param to_dt: End date for fetching candles.
        :return: List of Candle objects containing historical data.
        """
        df = self.download_intraday_chunked(
            symbol,
            from_dt,
            to_dt,
        )
        return [self.create_candle_from_row(row, row.name) for _, row in df.iterrows()]

    def create_candle_from_row(self, row: pd.Series, timestamp: pd.Timestamp) -> Candle:
        def to_scalar(val):
            if isinstance(val, pd.Series):
                return float(val.values[0])
            return float(val)

        return Candle(
            open=to_scalar(row["Open"]),
            high=to_scalar(row["High"]),
            low=to_scalar(row["Low"]),
            close=to_scalar(row["Close"]),
            volume=to_scalar(row["Volume"]),
            vwap=-1,  # you can compute this if needed
            timestamp=timestamp,
        )

    def download_intraday_chunked(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "5m",
        chunk_days: int = 7,
    ) -> pd.DataFrame:
        """
        Download intraday data from Yahoo Finance in chunks to bypass the 8-day limit.

        Args:
            symbol (str): Yahoo Finance symbol (e.g., "^SPX")
            start (datetime): Start datetime
            end (datetime): End datetime
            interval (str): Data interval (must be '1m' for this use case)
            chunk_days (int): Number of days per chunk (7 or less recommended)

        Returns:
            pd.DataFrame: Combined DataFrame with full data
        """
        all_data = []

        current_start = start
        while current_start < end:
            current_end = min(current_start + timedelta(days=chunk_days), end)
            print(f"Fetching: {current_start.date()} to {current_end.date()}")

            try:
                df = yf.download(
                    symbol,
                    start=current_start.strftime("%Y-%m-%d"),
                    end=current_end.strftime("%Y-%m-%d"),
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                )
                if not df.empty:
                    all_data.append(df)
            except Exception as e:
                print(f"Failed to download {current_start} to {current_end}: {e}")

            current_start = current_end

        if all_data:
            return pd.concat(all_data).sort_index()
        else:
            return pd.DataFrame()  # return empty if all fail
