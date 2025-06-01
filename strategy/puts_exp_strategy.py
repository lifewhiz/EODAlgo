from datetime import time
from data.models import Contract, ContractType
from strategy.base_strategy import BaseStrategy
from tester.models import CandleModel
from pandera.typing import DataFrame


class PutsExpirationStrategy(BaseStrategy):
    def __init__(self, symbol: str):
        super().__init__(symbol=symbol)
        self.buy_time = time(19, 35)  # 3:35 PM Eastern (19:35 UTC)

    def entry(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        return (
            contract.contract_type == ContractType.PUT
            and self.get_current_time(option_candles) >= self.buy_time
        )

    def exit(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        return False
