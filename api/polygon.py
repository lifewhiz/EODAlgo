from datetime import datetime
from typing import List
from polygon import RESTClient
from api.base import BaseAPI
from models import Candle
import arrow
import os

API_KEY = os.environ["POLYGON_API_KEY"]


class PolygonAPI(BaseAPI):
    """
    Polygon.io API implementation for fetching option contract candles.
    """

    def __init__(self):
        self.client = RESTClient(api_key=API_KEY)

    def convert_dt(self, dt: datetime) -> str:
        """
        Converts a datetime object to a string in 'YYYY-MM-DD' format.

        :param dt: Datetime object to convert.
        :return: Formatted date string.
        """
        return dt.strftime("%Y-%m-%d")

    def get_option_contract_candles(
        self, contract_symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        list_dt = list(
            self.client.list_aggs(
                contract_symbol,
                1,
                "minute",
                self.convert_dt(from_dt),
                self.convert_dt(to_dt),
                adjusted="true",
                sort="asc",
                limit=390,  # Trading hours
            )
        )
        return [
            Candle(
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                vwap=candle.vwap,
                timestamp=arrow.get(candle.timestamp).datetime,
            )
            for candle in list_dt
        ]

    def get_stock_candles(
        self, symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        raise NotImplementedError(
            "Polygon API does not support fetching stock candles directly."
        )
