from datetime import datetime, date, timedelta, time
from data.api.yahoo import YahooAPI
from data.options.process_0dte import load_contracts_from_json
from data.stocks.process_stocks import ProcessStocks
from data.models import ContractType, Candle
import pandas_market_calendars as mcal


START_DT = date.fromisoformat("2025-01-01")
END_DT = date.fromisoformat("2025-05-30")

BUY_TIME_UTC = time(19, 35)  # 3:35 PM ET
EOD_TIME_UTC = time(19, 59)  # 3:59 PM ET

STOCK_SYMBOL = "^SPX"
OPTION_SYMBOL = "SPXW"


def find_candle_at_or_after(
    candles: list[Candle], target_time: time, target_date: date
) -> Candle | None:
    for candle in candles:
        if (
            candle.timestamp.date() == target_date
            and candle.timestamp.time() >= target_time
        ):
            return candle
    return None


def parse_dt(dt: datetime) -> str:
    """
    Converts a datetime object to a string in 'YYYY-MM-DD' format.

    :param dt: Datetime object to convert.
    :return: Formatted date string.
    """
    return dt.strftime("%Y-%m-%d")


def run_intrinsic_value_put_strategy():
    contracts = load_contracts_from_json(OPTION_SYMBOL)

    stocks_api = YahooAPI()
    stocks_process = ProcessStocks(stocks_api)
    stock_candles = stocks_process.load_stocks(STOCK_SYMBOL)

    open_market_days = set(
        list(
            parse_dt(dt)
            for dt in mcal.get_calendar("NYSE")
            .valid_days(start_date=parse_dt(START_DT), end_date=parse_dt(END_DT))
            .to_pydatetime()
        )
    )

    results = []

    current_date = START_DT

    while current_date <= END_DT:
        if parse_dt(current_date) not in open_market_days:
            current_date += timedelta(days=1)
            continue

        # Filter contracts expiring on this day and are puts
        daily_contracts = [
            c
            for c in contracts
            if c.expiry.date() == current_date and c.contract_type == ContractType.PUT
        ]

        if not daily_contracts:
            print(f"No contracts found for {current_date}. Skipping.")
            current_date += timedelta(days=1)
            continue

        for contract in daily_contracts:
            buy_candle = find_candle_at_or_after(
                contract.data, BUY_TIME_UTC, current_date
            )
            if not buy_candle:
                print(
                    f"No buy candle found for {contract.symbol} on {current_date}. Skipping."
                )
                continue

            eod_stock_candle = find_candle_at_or_after(
                stock_candles, EOD_TIME_UTC, current_date
            )
            if not eod_stock_candle:
                print(
                    f"No EOD stock candle found for {STOCK_SYMBOL} on {current_date}. Skipping."
                )
                continue

            buy_price = (buy_candle.high + buy_candle.low) / 2
            stock_close = eod_stock_candle.close
            intrinsic_value = max(
                0,
                (
                    contract.strike - stock_close
                    if contract.contract_type == ContractType.PUT
                    else stock_close - contract.strike
                ),
            )
            profit = (intrinsic_value - buy_price) * 100
            pct_return = (profit / (buy_price * 100)) * 100 if buy_price != 0 else 0

            results.append(
                {
                    "symbol": contract.symbol,
                    "expiry": str(current_date),
                    "strike": contract.strike,
                    "buy_price": buy_price,
                    "underlying_close": stock_close,
                    "intrinsic_value": intrinsic_value,
                    "profit": profit,
                    "percent_return": pct_return,
                }
            )

        current_date += timedelta(days=1)

    return results


if __name__ == "__main__":
    results = run_intrinsic_value_put_strategy()

    total_profit = sum(r["profit"] for r in results)
    avg_return = (
        sum(r["percent_return"] for r in results) / len(results) if results else 0
    )

    wins = [r for r in results if r["profit"] > 0]
    losses = [r for r in results if r["profit"] < 0]

    win_rate = (len(wins) / len(results)) * 100 if results else 0
    avg_gain = sum(r["profit"] for r in wins) / len(wins) if wins else 0
    avg_loss = sum(r["profit"] for r in losses) / len(losses) if losses else 0
    risk_reward = (avg_gain / abs(avg_loss)) if avg_loss != 0 else float("inf")

    print(f"Total P&L: {total_profit:.2f}")
    print(f"Average Return: {avg_return:.2f}%")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Avg Gain: {avg_gain:.2f}, Avg Loss: {avg_loss:.2f}")
    print(f"Risk-Reward Ratio: {risk_reward:.2f}")
    print()

    for r in results:
        print(
            f"{r['symbol']} | {r['expiry']} | Strike: {r['strike']} | "
            f"Buy: {r['buy_price']:.2f} → IV: {r['intrinsic_value']:.2f} → "
            f"P&L: {r['profit']:.2f} ({r['percent_return']:.1f}%)"
        )
