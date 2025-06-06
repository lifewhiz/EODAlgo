from datetime import time
from data.models import Contract, ContractType
from strategy.base_strategy import BaseStrategy
from tester.models import CandleModel
from pandera.typing import DataFrame

import talib

BUY_TIME = time(19, 30)  # 30 minutes before close


class SmaRsiStrategy(BaseStrategy):
    def __init__(self, symbol: str):
        super().__init__(symbol=symbol)

    def entry(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        if self.get_current_time(option_candles) < BUY_TIME:
            return False

        close = stock_candles["close"].values  # talib expects a NumPy array

        rsi = talib.RSI(close, timeperiod=14)
        sma_20 = talib.SMA(close, timeperiod=20)
        sma_50 = talib.SMA(close, timeperiod=50)

        latest_rsi = rsi[-1]
        latest_sma_20 = sma_20[-1]
        latest_sma_50 = sma_50[-1]

        if (
            contract.contract_type == ContractType.CALL
            and latest_sma_20 > latest_sma_50
            and latest_rsi > 55
        ):
            return True

        if (
            contract.contract_type == ContractType.PUT
            and latest_sma_20 < latest_sma_50
            and latest_rsi < 45
        ):
            return True

        return False

    def exit(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        return False  # Held until expiration
