from abc import ABC, abstractmethod
from datetime import date, time
from typing import Optional
import pandas as pd
from portfolio.models import Trade
from portfolio.portfolio import Portfolio
from tester.models import CandleModel
from data.models import Contract, ContractType
from pandera.typing import DataFrame

MARKET_CLOSE = time(20, 0)  # 4:00 PM ET (20:00 UTC)


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

    def get_current_time(self, candles: DataFrame[CandleModel]) -> time:
        return self.get_current_op_candle(candles).timestamp.time()

    def get_current_op_candle(self, candles: DataFrame[CandleModel]) -> CandleModel:
        return candles.iloc[-1]

    def compute_mid_price(self, candle: CandleModel) -> Optional[float]:
        return (candle.high + candle.low) / 2

    def _compute_exit_result(
        self,
        stock_close: float,
        contract: Contract,
        current_date: date,
        current_time: time,
        buy_price: float,
        mid_price: float,
    ) -> Trade:
        if current_time == MARKET_CLOSE:
            final_price = max(
                0,
                (
                    contract.strike - stock_close
                    if contract.contract_type == ContractType.PUT
                    else stock_close - contract.strike
                ),
            )
        else:
            final_price = mid_price

        profit = (final_price - buy_price) * 100
        pct_return = (profit / (buy_price * 100)) * 100 if buy_price else 0

        return Trade(
            symbol=contract.symbol,
            expiry=current_date,
            strike=contract.strike,
            buy_price=buy_price,
            underlying_close=stock_close,
            intrinsic_value=final_price,
            profit=profit,
            percent_return=pct_return,
        )

    def exit_condition_met(
        self,
        contract: Contract,
        current_date: date,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
        buy_price: float,
    ) -> bool:
        current_op_candle = self.get_current_op_candle(option_candles)
        current_time = self.get_current_time(option_candles)
        if (
            self.exit(contract, option_candles, stock_candles)
            or current_time == MARKET_CLOSE
        ):
            trade = self._compute_exit_result(
                stock_close=stock_candles.iloc[-1].close,
                contract=contract,
                current_date=current_date,
                current_time=current_time,
                buy_price=buy_price,
                mid_price=self.compute_mid_price(current_op_candle),
            )
            self.portfolio.record_trade(trade)
            return True
        return False
