from datetime import time
from typing import Dict, Optional

from data.models import Contract, ContractType
from strategy.base_strategy import BaseStrategy
from tester.models import CandleModel
from pandera.typing import DataFrame
import talib

BUY_TIME = time(19, 45)
BUF = 5
MIN_PREMIUM = 1.0
MIN_RANGE_PCT = 0.005

STOP_LOSS = 0.5
TAKE_PROFIT = 1.0


class ExpStrategy(BaseStrategy):
    def __init__(self, symbol: str):
        super().__init__(symbol=symbol)

    def entry(
        self,
        option_map: Dict[Contract, DataFrame[CandleModel]],
        stock_candles: DataFrame[CandleModel],
    ) -> Optional[Contract]:
        if self.get_current_time(stock_candles) < BUY_TIME:
            return None

        current_price = self.get_current_candle(stock_candles).close
        high = stock_candles["high"].max()
        low = stock_candles["low"].min()

        if (high - low) / low < MIN_RANGE_PCT:
            return None

        close_prices = stock_candles["close"].values
        ma_short = talib.SMA(close_prices, timeperiod=10)[-1]
        ma_long = talib.SMA(close_prices, timeperiod=20)[-1]

        is_near_high = abs(current_price - high) < abs(current_price - low)
        if is_near_high and ma_short < ma_long:
            target_strike = current_price + BUF
            candidates = {
                c: candles
                for c, candles in option_map.items()
                if c.contract_type == ContractType.CALL
                and c.strike >= target_strike
                and candles.iloc[-1].close >= MIN_PREMIUM
            }
            if not candidates:
                return None
            return min(candidates.keys(), key=lambda c: c.strike)

        elif not is_near_high and ma_short > ma_long:
            target_strike = current_price - BUF
            candidates = {
                c: candles
                for c, candles in option_map.items()
                if c.contract_type == ContractType.PUT
                and c.strike <= target_strike
                and candles.iloc[-1].close >= MIN_PREMIUM
            }
            if not candidates:
                return None
            return max(candidates.keys(), key=lambda c: c.strike)

        return None

    def exit(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        position = self.portfolio.get_position(contract.symbol)
        return position.pct_change <= -STOP_LOSS or position.pct_change >= TAKE_PROFIT
