from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class ContractType(Enum):
    CALL = "call"
    PUT = "put"


@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float
    timestamp: datetime


@dataclass
class Contract:
    symbol: str
    underlying_symbol: str
    expiry: datetime
    strike: float
    contract_type: ContractType
    data: List[Candle]
