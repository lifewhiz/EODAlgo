from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List, Dict
import pandas as pd
from pandera.typing import DataFrame
from data.models import Contract, ContractType
from tester.models import CandleModel
from strategy.base_strategy import MARKET_CLOSE
import os


def compute_expiry_gains(
    contracts: List[Contract],
    stock_candles_by_date: Dict[str, DataFrame[CandleModel]],
) -> List[float]:
    """
    Calculate % gain if each contract was bought and held to expiry (EOD).
    """
    percent_gains = []

    for contract in contracts:
        date_str = contract.expiry.strftime("%Y-%m-%d")
        stock_df = stock_candles_by_date.get(date_str)

        stock_close = stock_df[stock_df["timestamp"].dt.time <= MARKET_CLOSE][
            "close"
        ].iloc[-1]

        # Use last candle as entry (assumption: bought just before market close)
        expiry_date = contract.expiry
        entry_time = (
            datetime.combine(expiry_date, MARKET_CLOSE) - timedelta(minutes=30)
        ).time()
        entry_candle = next(
            (c for c in contract.data if c.timestamp.time() >= entry_time), None
        )
        buy_price = (entry_candle.high + entry_candle.low) / 2

        # Intrinsic value at expiry
        if contract.contract_type == ContractType.CALL:
            intrinsic_value = max(0, stock_close - contract.strike)
        else:  # ContractType.PUT
            intrinsic_value = max(0, contract.strike - stock_close)

        profit = intrinsic_value - buy_price
        percent_gain = (profit / buy_price) * 100 if buy_price else 0
        percent_gains.append(percent_gain)

    return percent_gains


def plot_expiry_gains(
    contracts: List[Contract],
    stock_candles_by_date: Dict[str, DataFrame[CandleModel]],
):
    gains = compute_expiry_gains(contracts, stock_candles_by_date)
    if not gains:
        print("No data to plot.")
        return

    df = pd.DataFrame({"Gain": gains})

    bins = [-np.inf, -5, 5, np.inf]
    labels = ["Loss (< -5%)", "Breakeven (-5% to 5%)", "Gain (> 5%)"]
    palette = {
        "Loss (< -5%)": "red",
        "Breakeven (-5% to 5%)": "gold",
        "Gain (> 5%)": "green",
    }

    df["Category"] = pd.cut(df["Gain"], bins=bins, labels=labels)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [2, 1]}
    )

    for category in labels:
        subset = df[df["Category"] == category]
        sns.ecdfplot(
            data=subset,
            x="Gain",
            stat="proportion",
            ax=ax1,
            color=palette[category],
            label=category,
        )

    ax1.set_xscale("symlog")
    ax1.set_xlabel("% Gain (Symlog Scale)")
    ax1.set_ylabel("Proportion")
    ax1.set_title("ECDF of Expiry PnL")
    ax1.legend(title="Category")

    count_data = df["Category"].value_counts().reindex(labels, fill_value=0)
    ax2.bar(
        count_data.index,
        count_data.values,
        color=[palette[label] for label in count_data.index],
    )
    ax2.set_ylabel("Number of Contracts")
    ax2.set_title("Count per Gain Category")

    plt.tight_layout()
    plt.savefig(os.path.join("artifacts", "expiry_gains.png"))
