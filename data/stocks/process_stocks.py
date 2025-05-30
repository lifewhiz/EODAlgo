from datetime import datetime
import json
from typing import List
from pathlib import Path

from api.base import BaseAPI
from models import Candle
import os

BASE_DIR = Path("data/storage/stocks")
os.makedirs(BASE_DIR, exist_ok=True)


class ProcessStocks:
    def __init__(self, api: BaseAPI):
        self.api = api

    def fetch_stocks(self, symbol: str, from_dt: datetime, to_dt: datetime):
        """
        Fetches stock data for the given list of stocks.
        This method should be implemented to fetch data from a specific API.
        """
        if not (stock_data := self.load_stocks(symbol)):
            stock_data = self.api.get_stock_candles(
                symbol=symbol,
                from_dt=from_dt,
                to_dt=to_dt,
            )
            self.save_candles_to_json(stock_data, f"{symbol}.json")
        return stock_data

    def load_stocks(self, symbol: str) -> List[Candle]:
        """
        Loads stock data from a JSON file.
        :param symbol: Stock symbol to load data for.
        :return: List of Candle objects.
        """
        file_path = f"{BASE_DIR}/{symbol}.json"
        if not os.path.exists(file_path):
            return []

        with open(file_path, "r") as f:
            raw_data = json.load(f)

        return [
            Candle(
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
                vwap=c["vwap"],
                timestamp=datetime.fromisoformat(c["timestamp"]),
            )
            for c in raw_data
        ]

    def save_candles_to_json(self, candles: List[Candle], file_path: str):
        with open(f"{BASE_DIR}/{file_path}", "w") as f:
            json.dump(
                [
                    {
                        "open": c.open,
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "volume": c.volume,
                        "vwap": c.vwap,
                        "timestamp": c.timestamp.isoformat(),
                    }
                    for c in candles
                ],
                f,
                indent=2,
            )
