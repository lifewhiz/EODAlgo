from datetime import datetime
from typing import List
from data.api.base import BaseAPI
from data.models import Candle


class MockAPI(BaseAPI):
    """
    Mock implementation of BaseAPI for testing purposes.
    """

    def get_option_contract_candles(
        self, contract_symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        """
        Returns mock candle data for a specific option contract.

        :param contract_symbol: The symbol of the option contract.
        :param from_dt: Start date for fetching candles.
        :param to_dt: End date for fetching candles.
        :return: List of Candle objects containing mock data.
        """
        # Generate mock candle data
        return [
            Candle(
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000,
                vwap=100.5,
                timestamp=from_dt,
            )
            for _ in range(10)  # Return 10 mock candles
        ]

    def get_stock_candles(
        self, symbol: str, from_dt: datetime, to_dt: datetime) -> List[Candle]:
        """"
        "Returns mock candle data for a specific stock."
        """
        # Generate mock stock candle data
        return [
            Candle(
                open=200.0,
                high=210.0,
                low=190.0,
                close=205.0,
                volume=5000,
                vwap=202.5,
                timestamp=from_dt,
            )
            for _ in range(10)  # Return 10 mock candles
        ]