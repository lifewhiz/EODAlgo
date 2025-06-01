from datetime import time
from typing import Dict, List
import numpy as np
from pandera.typing import DataFrame
from tester.models import CandleModel
import matplotlib.pyplot as plt
import os


def compute_eod_movements(
    stock_candles_by_date: Dict[str, DataFrame[CandleModel]],
) -> List[float]:
    changes = []
    for df in stock_candles_by_date.values():
        eod_df = df[df["timestamp"].dt.time >= time(19, 30)]
        if len(eod_df) < 2:
            continue
        open_price = eod_df.iloc[0].open
        close_price = eod_df.iloc[-1].close
        pct_change = ((close_price - open_price) / open_price) * 100
        changes.append(pct_change)
    return changes


def plot_direction_clusters(
    stock_candles_by_date: Dict[str, DataFrame[CandleModel]],
):
    """
    Show how often SPX made large directional moves in last 30 min,
    with threshold computed from 75th percentile of movement.
    """
    eod_changes = compute_eod_movements(stock_candles_by_date)
    if not eod_changes:
        print("No valid EOD changes to compute threshold.")
        return

    threshold = np.percentile(np.abs(eod_changes), 50)

    up, down, flat = 0, 0, 0

    for change in eod_changes:
        if change >= threshold:
            up += 1
        elif change <= -threshold:
            down += 1
        else:
            flat += 1

    labels = ["UP", "DOWN", "FLAT"]
    values = [up, down, flat]
    colors = ["green", "red", "gray"]

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=colors)
    plt.title(f"EOD SPX Direction Clusters (Pct_Threshold ≈ {threshold:.2f}%)")
    plt.ylabel("Number of Days")
    plt.tight_layout()
    plt.savefig(os.path.join("artifacts", "direction_clusters.png"))
