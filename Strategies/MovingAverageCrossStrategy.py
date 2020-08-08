from Strategies.strategy import Strategy
import numpy as np
import datetime
from event import SignalEvent


class MovingAverageCrossStrategy(Strategy):
    """
    用来进行基本的移动平均跨越测录的实现，这个策略有一组短期和长期的简单移动平均值。
    默认的短期/长期的窗口分别是100天和400天。
    """

    def __init__(
            self, bars, events, short_window=100, long_window=400
    ):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        """
        给bought字典增加键，对于所有的代码都设置值为OUT
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):
        """
        基于MAC SMA生成一组新的信号，进入市场的标志就是短期的移动平均超过
        长期的移动平均。
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(
                    s, "adj_close", N=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(s)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ""
                    order_price = self.bars.get_latest_bars_values(s, 'adj_close')
                    if short_sma > long_sma and self.bought[s] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = 'LONG'
                        signal = SignalEvent(1, bar_date, symbol, dt, sig_dir, order_price, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == "LONG":
                        print("SHORT:%s" % bar_date)
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, bar_date, symbol, dt, sig_dir, order_price, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'
