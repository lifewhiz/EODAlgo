from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from data.models import Contract, ContractType
from tester.models import CandleModel
from constants import MARKET_CLOSE


@dataclass
class Position:
    contract: Contract
    entry_option_candle: CandleModel
    entry_time: datetime = field(init=False)
    entry_price: float = field(init=False)
    exit_price: Optional[float] = None
    closed: bool = False
    exit_option_candle: Optional[CandleModel] = None
    stock_close: Optional[float] = None
    pnl: Optional[float] = None
    pct_change: Optional[float] = None

    def __post_init__(self):
        self.entry_time = self.entry_option_candle.timestamp
        self.entry_price = self.get_mid_price(self.entry_option_candle)

    def get_mid_price(self, candle: CandleModel) -> float:
        return (candle.high + candle.low) / 2

    def close(self, exit_option_candle: CandleModel, stock_close: float) -> None:
        assert not self.closed, "Position already closed"

        self.closed = True
        self.exit_option_candle = exit_option_candle

        self.stock_close = stock_close
        self.exit_price = self._calculate_exit_price(exit_option_candle, stock_close)

        self.pnl = (self.exit_price - self.entry_price) * 100
        self.pct_change = self.pnl / self.entry_price

    def _calculate_exit_price(
        self, exit_option_candle: CandleModel, stock_close: float
    ) -> float:
        current_time = exit_option_candle.timestamp.time()

        if current_time == MARKET_CLOSE:
            if self.contract.contract_type == ContractType.PUT:
                return max(0, self.contract.strike - stock_close)
            else:
                return max(0, stock_close - self.contract.strike)
        else:
            return self.get_mid_price(exit_option_candle)

    def summary(self) -> str:
        if not self.closed:
            print("Position is still open.")
        print(
            f"Position Summary:\n"
            f"Symbol: {self.contract.symbol}\n"
            f"Expiry: {self.contract.expiry}\n"
            f"Strike: {self.contract.strike}\n"
            f"P&L: {self.pnl:.2f}\n"
            f"Percent Change: {self.pct_change:.2f}%"
        )
