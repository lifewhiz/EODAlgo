from typing import Dict, List
from portfolio.models import Position


class Portfolio:
    def __init__(self):
        self.positions_dt: Dict[str, Position] = dict()

    def record_position(self, symbol: str, position: Position):
        self.positions_dt[symbol] = position

    def get_position(self, symbol: str) -> Position:
        return self.positions_dt[symbol]

    def summary(self):
        positions = list(self.positions_dt.values())
        position_count = len(positions)

        total_profit = sum(p.pnl for p in positions)
        total_return = sum(p.pct_change for p in positions)
        avg_return = total_return / position_count if position_count else 0

        wins = [p for p in positions if p.pnl > 0]
        losses = [p for p in positions if p.pnl < 0]
        win_rate = (len(wins) / position_count) * 100 if position_count else 0
        avg_gain = sum(p.pnl for p in wins) / len(wins) if wins else 0
        avg_loss = sum(p.pnl for p in losses) / len(losses) if losses else 0
        risk_reward = avg_gain / abs(avg_loss) if avg_loss != 0 else float("inf")

        print(f"Total P&L: {total_profit:.2f}")
        print(f"Average Return: {avg_return:.2f}%")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Avg Gain: {avg_gain:.2f}, Avg Loss: {avg_loss:.2f}")
        print(f"Risk-Reward Ratio: {risk_reward:.2f}\n")

        for p in positions:
            print(
                f"{p.contract.symbol} | {p.contract.expiry} | Strike: {p.contract.strike} | {p.entry_price:.2f} → {p.exit_price:.2f} | P&L: {p.pnl:.2f} ({p.pct_change:.1f}%)"
            )
