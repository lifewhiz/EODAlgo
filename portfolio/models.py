from dataclasses import dataclass
from datetime import date


@dataclass
class Trade:
    symbol: str
    expiry: date
    strike: float
    buy_price: float
    underlying_close: float
    intrinsic_value: float
    profit: float
    percent_return: float
