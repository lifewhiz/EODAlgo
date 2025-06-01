from abc import ABC, abstractmethod
from datetime import date, time
from typing import Optional
from constants import MARKET_CLOSE
from portfolio.models import Position
from portfolio.portfolio import Portfolio
from tester.models import CandleModel
from data.models import Contract, ContractType
from pandera.typing import DataFrame


class BaseStrategy(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.portfolio = Portfolio()

    @abstractmethod
    def entry(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        pass

    @abstractmethod
    def exit(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        pass

    def entry_wrapper(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        if self.entry(contract, option_candles, stock_candles):
            current_op_candle = self.get_current_candle(option_candles)
            position = Position(
                contract=contract,
                entry_option_candle=current_op_candle,
            )
            self.portfolio.record_position(contract.symbol, position)
            return True
        return False

    def exit_wrapper(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        current_op_candle = self.get_current_candle(option_candles)
        current_time = self.get_current_time(option_candles)

        if (
            self.exit(contract, option_candles, stock_candles)
            or current_time == MARKET_CLOSE
        ):
            position = self.portfolio.get_position(contract.symbol)
            position.close(
                exit_option_candle=current_op_candle,
                stock_close=stock_candles.iloc[-1].close,
            )
            return True
        return False

    def get_current_time(self, candles: DataFrame[CandleModel]) -> time:
        return self.get_current_candle(candles).timestamp.time()

    def get_current_candle(self, candles: DataFrame[CandleModel]) -> CandleModel:
        return candles.iloc[-1]
