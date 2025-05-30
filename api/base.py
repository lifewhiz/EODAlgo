from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from models import Candle, ContractType


class BaseAPI(ABC):

    @abstractmethod
    def get_option_contract_candles(
        self, contract_symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        """
        Fetches historical candle data for a specific option contract.

        :param contract_symbol: The symbol of the option contract.
        :param from_dt: Start date for fetching candles.
        :param to_dt: End date for fetching candles.
        :return: List of Candle objects containing historical data.
        """
        pass

    @abstractmethod
    def get_stock_candles(
        self, symbol: str, from_dt: datetime, to_dt: datetime
    ) -> List[Candle]:
        """
        Fetches historical candle data for a specific stock.

        :param symbol: The stock symbol.
        :param from_dt: Start date for fetching candles.
        :param to_dt: End date for fetching candles.
        :return: List of Candle objects containing historical data.
        """
        pass

    @staticmethod
    def format_occ_option_symbol(
        symbol: str, exp_date: datetime, contract_type: ContractType, strike: float
    ) -> str:
        """
        Formats an OCC option symbol (e.g., O:SPY251219C00650000)

        Args:
            symbol (str): Underlying ticker symbol (e.g., "SPY")
            exp_date (date): Expiration date as a datetime.date object
            contract_type (ContractType): ContractType.CALL or ContractType.PUT
            strike (float): Strike price (e.g., 650.0)

        Returns:
            str: OCC formatted option symbol
        """
        # Convert expiration date to YYMMDD
        occ_date = exp_date.strftime("%y%m%d")

        # Convert strike to 8-digit padded string (multiply by 1000)
        occ_strike = f"{int(strike * 1000):08d}"

        return (
            f"O:{symbol.upper()}{occ_date}{contract_type.value[0].upper()}{occ_strike}"
        )
