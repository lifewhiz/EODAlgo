from typing import List
from portfolio.models import Trade


class Portfolio:
    def __init__(self):
        self.trades: List[Trade] = []
        self.active_trades: List[Trade] = []
        self.total_profit = 0.0
        self.total_return = 0.0
        self.trade_count = 0

    def record_trade(self, trade: Trade):
        self.trades.append(trade)
        self.active_trades.append(trade)
        self.total_profit += trade.profit
        self.total_return += trade.percent_return
        self.trade_count += 1

    def summary(self):
        total_profit = self.total_profit
        avg_return = self.total_return / self.trade_count if self.trade_count else 0
        wins = [t for t in self.trades if t.profit > 0]
        losses = [t for t in self.trades if t.profit < 0]
        win_rate = (len(wins) / self.trade_count) * 100 if self.trade_count else 0
        avg_gain = sum(t.profit for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.profit for t in losses) / len(losses) if losses else 0
        risk_reward = avg_gain / abs(avg_loss) if avg_loss != 0 else float("inf")

        print(f"Total P&L: {total_profit:.2f}")
        print(f"Average Return: {avg_return:.2f}%")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Avg Gain: {avg_gain:.2f}, Avg Loss: {avg_loss:.2f}")
        print(f"Risk-Reward Ratio: {risk_reward:.2f}\n")

        for t in self.trades:
            print(
                f"{t.symbol} | {t.expiry} | Strike: {t.strike} | Buy: {t.buy_price:.2f} → IV: {t.intrinsic_value:.2f} → P&L: {t.profit:.2f} ({t.percent_return:.1f}%)"
            )
