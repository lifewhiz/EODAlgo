from datetime import time
from data.models import Contract, ContractType
from strategy.base_strategy import BaseStrategy
from tester.models import CandleModel
from pandera.typing import DataFrame

BUY_TIME = time(19, 35)


class PutsExpirationStrategy(BaseStrategy):
    def __init__(self, symbol: str):
        super().__init__(symbol=symbol)

    def entry(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        return (
            contract.contract_type == ContractType.PUT
            and self.get_current_time(option_candles) >= BUY_TIME
        )

    def exit(
        self,
        contract: Contract,
        option_candles: DataFrame[CandleModel],
        stock_candles: DataFrame[CandleModel],
    ) -> bool:
        return False
