from analysis.activation import plot_activation_times
from analysis.direction import plot_direction_clusters
from analysis.expiry import plot_expiry_gains
from data.data_handler import DataHandler


def analysis_command(symbol: str):
    print(f"Running EOD analysis for {symbol}...")

    handler = DataHandler(symbol)

    all_contracts = []
    for daily_contracts in handler.contracts_by_date.values():
        all_contracts.extend(daily_contracts)

    print(f"Total contracts loaded: {len(all_contracts)}")

    print("→ Plotting activation time clusters")
    plot_activation_times(contracts=all_contracts)

    print("→ Plotting EOD movement clusters")
    plot_direction_clusters(handler.stock_candles_dt_df)

    print("→ Plotting expiry gain histogram")
    plot_expiry_gains(
        contracts=all_contracts,
        stock_candles_by_date=handler.stock_candles_dt_df,
    )
