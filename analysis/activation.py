import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from data.models import Contract
from typing import List
import os


def compute_contract_jump_threshold(contracts: List[Contract]) -> float:
    jumps = []
    for c in contracts:
        candles = c.data
        if not candles:
            continue
        candles_sorted = sorted(candles, key=lambda x: x.timestamp)
        last_30_minutes_candles = candles_sorted[-30:]

        for i in range(0, len(last_30_minutes_candles), 5):
            five_min_candles = last_30_minutes_candles[i : i + 5]
            jump = max(c.high for c in five_min_candles) - min(
                c.low for c in five_min_candles
            )
            jumps.append(jump)

    return pd.Series(jumps).quantile(0.75)


def gather_activation_records(
    contracts: List[Contract],
    jump_threshold: float,
) -> pd.DataFrame:
    records = []

    for contract in contracts:
        candles_by_datetime = {
            c.timestamp.replace(tzinfo=None): c for c in contract.data
        }

        for i in range(0, 30, 5):
            start_dt = datetime.combine(
                contract.expiry, datetime.min.time()
            ) + timedelta(hours=19, minutes=30 + i)

            t = start_dt.time()
            candle = candles_by_datetime.get(start_dt)
            if not candle:
                continue

            next_5_min_candles = [
                c
                for minute_offset in range(1, 6)
                if (
                    c := candles_by_datetime.get(
                        start_dt + timedelta(minutes=minute_offset)
                    )
                )
            ]
            if not next_5_min_candles:
                continue

            max_high = max(c.high for c in next_5_min_candles)
            jump = max_high - candle.close
            activated = jump >= jump_threshold

            records.append(
                {
                    "time": t.strftime("%H:%M"),
                    "contract_type": contract.contract_type.name,
                    "activation_status": "Activated" if activated else "Not Activated",
                }
            )

    return pd.DataFrame(records)


def plot_activation_times(
    contracts: List[Contract],
):
    jump_threshold = compute_contract_jump_threshold(contracts)
    df = gather_activation_records(contracts, jump_threshold)

    if df.empty:
        print("No data to plot.")
        return

    df["time"] = pd.Categorical(
        df["time"], categories=sorted(df["time"].unique()), ordered=True
    )

    color_map_call = {
        "Activated": "green",
        "Not Activated": "red",
    }

    color_map_put = {
        "Activated": "blue",
        "Not Activated": "orange",
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 5))

    call_data = df[df["contract_type"] == "CALL"]
    call_counts = (
        call_data.groupby(["time", "activation_status"], observed=False)
        .size()
        .reset_index(name="count")
    )

    sns.barplot(
        data=call_counts,
        x="time",
        y="count",
        hue="activation_status",
        palette=color_map_call,
        ax=ax1,
    )

    put_data = df[df["contract_type"] == "PUT"]
    put_counts = (
        put_data.groupby(["time", "activation_status"], observed=False)
        .size()
        .reset_index(name="count")
    )

    sns.barplot(
        data=put_counts,
        x="time",
        y="count",
        hue="activation_status",
        palette=color_map_put,
        ax=ax2,
    )

    ax1.set_title(
        f"Activation Times for CALL Contracts (Jump_Threshold ≈ {jump_threshold:.2f}%)",
        fontsize=14,
    )
    ax2.set_title(
        f"Activation Times for PUT Contracts (Jump_Threshold ≈ {jump_threshold:.2f}%)",
        fontsize=14,
    )

    ax1.set_xlabel("Time (HH:MM)", fontsize=12)
    ax1.set_ylabel("Count", fontsize=12)
    ax2.set_xlabel("Time (HH:MM)", fontsize=12)
    ax2.set_ylabel("Count", fontsize=12)

    ax1.set_xticks(np.arange(len(call_counts["time"].unique())))
    ax1.set_xticklabels(call_counts["time"].unique(), rotation=45)
    ax2.set_xticks(np.arange(len(put_counts["time"].unique())))
    ax2.set_xticklabels(put_counts["time"].unique(), rotation=45)

    handles, _ = ax1.get_legend_handles_labels()
    ax1.legend(
        handles=handles,
        labels=["CALL - Activated", "CALL - Not Activated"],
        title="Activation Status",
        fontsize=10,
    )

    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(
        handles=handles,
        labels=["PUT - Activated", "PUT - Not Activated"],
        title="Activation Status",
        fontsize=10,
    )

    sns.move_legend(ax1, bbox_to_anchor=(1, 0.5), loc="center left", frameon=False)
    sns.move_legend(ax2, bbox_to_anchor=(1, 0.5), loc="center left", frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join("artifacts", "activation_times.png"))
