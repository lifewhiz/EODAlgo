from enum import Enum
import os
import json
from dataclasses import asdict
from datetime import datetime
from typing import List
from pathlib import Path
from data.models import Candle, Contract, ContractType

BASE_DIR = Path("data/storage/options")
SYNTHETIC_BASE_DIR = Path("data/storage/synthetic_options")
os.makedirs(BASE_DIR, exist_ok=True)


# Custom JSON encoder to handle datetime and Enum serialization
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


# Function to save each Contract as a separate data.json file
def save_contracts_as_json(contracts: List[Contract]):
    for contract in contracts:
        file_path = os.path.join(BASE_DIR, f"{contract.symbol}.json")
        with open(file_path, "w") as f:
            json.dump(asdict(contract), f, cls=EnhancedJSONEncoder, indent=2)


def load_contracts_from_json(
    symbol: str, include_synthetic: bool = False
) -> List[Contract]:
    contracts = []
    dirs = [BASE_DIR, SYNTHETIC_BASE_DIR] if include_synthetic else [BASE_DIR]

    for base_dir in dirs:
        if not os.path.exists(base_dir):
            print(f"Directory {base_dir} does not exist. Skipping.")
            continue

        for file_name in os.listdir(base_dir):
            if not file_name.endswith(".json") or not symbol in file_name:
                continue

            file_path = os.path.join(base_dir, file_name)

            with open(file_path, "r") as f:
                raw = json.load(f)

            candles = [
                Candle(
                    open=c["open"],
                    high=c["high"],
                    low=c["low"],
                    close=c["close"],
                    volume=c["volume"],
                    vwap=c["vwap"],
                    timestamp=datetime.fromisoformat(c["timestamp"]),
                )
                for c in raw["data"]
            ]

            contract = Contract(
                symbol=raw["symbol"],
                underlying_symbol=raw["underlying_symbol"],
                expiry=datetime.fromisoformat(raw["expiry"]),
                strike=raw["strike"],
                contract_type=ContractType(raw["contract_type"]),
                data=candles,
            )

            contracts.append(contract)

    return contracts
