from abc import ABC, abstractmethod
from datetime import time
from constants import MARKET_CLOSE
from portfolio.models import Position
from portfolio.portfolio import Portfolio
from tester.models import CandleModel
from data.models import Contract
from pandera.typing import DataFrame
from typing import Dict, Optional


class BaseStrategy(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.portfolio = Portfolio()

    @abstractmethod
    def entry(
        self,
        contracts_to_candles: Dict[Contract, DataFrame[CandleModel]],
        stock_candles: DataFrame[CandleModel],
    ) -> Optional[Contract]:
        """
        Return the contract to enter, or None if no entry.
        """
        pass

    @abstractmethod
    def exit(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        """
        Return True if the position should be exited.
        """
        pass

    def entry_wrapper(
        self,
        contracts_to_candles: Dict[Contract, DataFrame[CandleModel]],
        stock_candles: DataFrame[CandleModel],
    ) -> Optional[Contract]:
        contract_to_enter = self.entry(contracts_to_candles, stock_candles)
        if contract_to_enter:
            op_candles = contracts_to_candles[contract_to_enter]
            current_op_candle = self.get_current_candle(op_candles)
            position = Position(
                contract=contract_to_enter,
                entry_option_candle=current_op_candle,
            )
            self.portfolio.record_position(contract_to_enter.symbol, position)
        return contract_to_enter

    def exit_wrapper(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        current_op_candle = self.get_current_candle(option_candles)
        current_time = self.get_current_time(option_candles)

        position = self.portfolio.get_position(contract.symbol)
        position.compute_metrics(current_op_candle, stock_candles.iloc[-1].close)

        if (
            self.exit(contract, option_candles, stock_candles)
            or current_time == MARKET_CLOSE
        ):
            position = self.portfolio.get_position(contract.symbol)
            position.close()
            return True
        return False

    def get_current_time(self, candles: DataFrame[CandleModel]) -> time:
        return self.get_current_candle(candles).timestamp.time()

    def get_current_candle(self, candles: DataFrame[CandleModel]) -> CandleModel:
        return candles.iloc[-1]
