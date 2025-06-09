import shutil
import numpy as np
from scipy.stats import norm
from tqdm import tqdm
from dataclasses import asdict
from datetime import datetime, time, timezone
import json
import os
from pathlib import Path
from typing import List
from pandera.typing import DataFrame

from constants import MARKET_CLOSE
from data.api.base import BaseAPI
from data.funcs import get_option_symbol
from data.models import Candle, Contract, ContractType
from data.options.process_0dte import EnhancedJSONEncoder, load_contracts_from_json
from data.data_handler import DataHandler
from tester.models import CandleModel

BASE_DIR = Path("data/storage/synthetic_options")
os.makedirs(BASE_DIR, exist_ok=True)


class SyntheticDataGenerator:
    def __init__(self, strike_step=5, strike_buffer=50, r=0.05, iv_skew_slope=0.0015):
        self.strike_step = strike_step
        self.strike_buffer = strike_buffer
        self.r = r
        self.iv_skew_slope = iv_skew_slope

    def bs_price(self, S, K, T, r, vol, contract_type: ContractType):
        if T <= 0:
            return (
                max(0, S - K) if contract_type == ContractType.CALL else max(0, K - S)
            )

        d1 = (np.log(S / K) + (r + 0.5 * vol**2) * T) / (vol * np.sqrt(T))
        d2 = d1 - vol * np.sqrt(T)

        if contract_type == ContractType.CALL:
            return S * norm.cdf(d1) - np.exp(-r * T) * K * norm.cdf(d2)
        else:
            return np.exp(-r * T) * K * norm.cdf(-d2) - S * norm.cdf(-d1)

    def bs_vega(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T)

    def implied_vol(self, price, S, K, T, r, contract_type: ContractType):
        if T <= 0:
            return 0.0

        max_iter = 100
        precision = 1e-5
        sigma = 0.5

        for _ in range(max_iter):
            model_price = self.bs_price(S, K, T, r, sigma, contract_type)
            vega = self.bs_vega(S, K, T, r, sigma)
            if vega == 0:
                break

            diff = price - model_price
            if abs(diff) < precision:
                return sigma

            sigma += diff / vega

        return sigma

    def _estimate_base_iv(
        self, candle_close: float, contract: Contract, S: float, T: float
    ) -> float:
        return self.implied_vol(
            candle_close, S, contract.strike, T, self.r, contract.contract_type
        )

    def _generate_chain_for_strike(
        self,
        symbol: str,
        contract: Contract,
        strike: float,
        stock_candles: DataFrame[CandleModel],
        option_candles: DataFrame[CandleModel],
        market_close: datetime,
    ) -> Contract:
        candles = []

        ts: datetime
        stock_candle: Candle
        for ts, stock_candle in stock_candles.iterrows():
            minutes_to_expiry = (market_close - ts).total_seconds() / 60
            assert (
                minutes_to_expiry >= 0
            ), "Market close time must be after stock candle time"

            T = (minutes_to_expiry / (60 * 6.5)) / 252
            option_candle = option_candles.loc[ts]
            base_iv = self._estimate_base_iv(
                option_candle.close, contract, stock_candle.close, T
            )
            iv = max(base_iv + self.iv_skew_slope * (contract.strike - strike), 0.01)

            candles.append(
                Candle(
                    open=self.bs_price(
                        stock_candle.open, strike, T, self.r, iv, contract.contract_type
                    ),
                    high=max(
                        self.bs_price(
                            stock_candle.low,
                            strike,
                            T,
                            self.r,
                            iv,
                            contract.contract_type,
                        ),
                        self.bs_price(
                            stock_candle.high,
                            strike,
                            T,
                            self.r,
                            iv,
                            contract.contract_type,
                        ),
                    ),
                    low=min(
                        self.bs_price(
                            stock_candle.low,
                            strike,
                            T,
                            self.r,
                            iv,
                            contract.contract_type,
                        ),
                        self.bs_price(
                            stock_candle.high,
                            strike,
                            T,
                            self.r,
                            iv,
                            contract.contract_type,
                        ),
                    ),
                    close=self.bs_price(
                        stock_candle.close,
                        strike,
                        T,
                        self.r,
                        iv,
                        contract.contract_type,
                    ),
                    volume=0.0,
                    vwap=0.0,
                    timestamp=ts,
                )
            )

        option_symbol = BaseAPI.format_occ_option_symbol(
            symbol=get_option_symbol(symbol),
            exp_date=contract.expiry,
            contract_type=contract.contract_type,
            strike=strike,
        )
        return Contract(
            symbol=option_symbol,
            underlying_symbol=contract.underlying_symbol,
            expiry=contract.expiry,
            strike=strike,
            contract_type=contract.contract_type,
            data=candles,
        )

    def _save_contracts_as_json(self, contracts: List[Contract]):
        for contract in tqdm(contracts, desc="Saving contracts"):
            file_path = os.path.join(BASE_DIR, f"{contract.symbol}.json")
            with open(file_path, "w") as f:
                json.dump(asdict(contract), f, cls=EnhancedJSONEncoder, indent=2)

    def _load_synthetic_contracts(self, symbol: str) -> List[Contract]:
        contracts: List[Contract] = []

        for file_name in os.listdir(BASE_DIR):
            if file_name.endswith(".json") and symbol in file_name:
                file_path = os.path.join(BASE_DIR, file_name)
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

                contracts.append(
                    Contract(
                        symbol=raw["symbol"],
                        underlying_symbol=raw["underlying_symbol"],
                        expiry=datetime.fromisoformat(raw["expiry"]),
                        strike=raw["strike"],
                        contract_type=ContractType(raw["contract_type"]),
                        data=candles,
                    )
                )

        return contracts

    def _process_date_group(
        self, symbol: str, contracts: List[Contract], handler: DataHandler
    ) -> List[Contract]:
        dt = contracts[0].expiry.date()
        stock_candles = handler.get_stock_candles(dt)
        market_close = datetime.combine(dt, MARKET_CLOSE, tzinfo=timezone.utc)
        gen_contracts = []

        for contract in tqdm(contracts, desc=f"Processing {dt}"):
            option_candles = handler.get_option_candles(contract.symbol)
            center = round(
                (stock_candles.iloc[0].open + stock_candles.iloc[-1].close) / 2
            )
            start = int(
                (center - self.strike_buffer) // self.strike_step * self.strike_step
            )
            end = int(
                (center + self.strike_buffer) // self.strike_step * self.strike_step
            )
            strikes = range(start, end + 1, self.strike_step)

            for strike in strikes:
                gen_contracts.append(
                    self._generate_chain_for_strike(
                        symbol=symbol,
                        contract=contract,
                        strike=strike,
                        stock_candles=stock_candles,
                        option_candles=option_candles,
                        market_close=market_close,
                    )
                )

        return gen_contracts

    def generate_synthetic_data(self, symbol: str) -> List[Contract]:
        handler = DataHandler(symbol)
        all_gen_contracts = []

        for _, contracts in handler.contracts_by_date.items():
            call = next(
                (c for c in contracts if c.contract_type == ContractType.CALL), None
            )
            put = next(
                (c for c in contracts if c.contract_type == ContractType.PUT), None
            )
            selected_contracts = [c for c in (call, put) if c is not None]

            all_gen_contracts.extend(
                self._process_date_group(symbol, selected_contracts, handler)
            )

        self._save_contracts_as_json(all_gen_contracts)
        return all_gen_contracts

    def clean_synthetic_data(self, symbol: str) -> List[Contract]:
        all_contracts = self._load_synthetic_contracts(symbol)
        cleaned_contracts: List[Contract] = []

        for contract in tqdm(all_contracts):
            if all(d.close <= 1000 for d in contract.data):
                cleaned_contracts.append(contract)

        print(
            f"Total contracts cleaned: {len(cleaned_contracts)} / {len(all_contracts)}"
        )
        shutil.rmtree(BASE_DIR)
        os.mkdir(BASE_DIR)
        self._save_contracts_as_json(cleaned_contracts)

        return cleaned_contracts
