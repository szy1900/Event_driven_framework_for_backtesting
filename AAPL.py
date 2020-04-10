# -*- coding: utf-8 -*-

# mac.py
from __future__ import print_function

import datetime

import numpy as np
import pandas as pd
import statsmodels.api as sm
import math
import os
from strategy import Strategy
from event import SignalEvent, OrderEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio

## Tasks to do:
## 1. Complete the sea turtle strategy
## 2. Multiple strategies
## 3. Run every day automatically
## 4. Sned text when one of the strategy find something
class My_portfolio(Portfolio):

    def generate_naive_order(self, signal):
        order=None
        date_time = signal.date_time
        symbol=signal.symbol
        direction=signal.signal_type
        strength=signal.strength
        order_price = signal.order_price
        all_in_cash = self.current_holdings['cash']
        mkt_quantity= math.floor(all_in_cash/order_price)
        cur_quantity=self.current_positions[symbol]
        order_type='MKT'

        if direction=='LONG' and cur_quantity==0:
            order=OrderEvent(date_time, symbol, order_type, mkt_quantity, 'BUY', order_price,direction)
        if direction=='SHORT' and cur_quantity==0:
            order=OrderEvent(date_time, symbol, order_type, mkt_quantity,'SELL', order_price,direction)
        if direction=='EXIT' and cur_quantity>0:
            order=OrderEvent(date_time, symbol, order_type, abs(cur_quantity), 'SELL', order_price,direction)
        if direction=='EXIT' and cur_quantity<0:
            order=OrderEvent(date_time, symbol, order_type, abs(cur_quantity), 'BUY', order_price,direction)

        return order


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
                        signal = SignalEvent(1, bar_date, symbol, dt, sig_dir, order_price ,1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == "LONG":
                        print("SHORT:%s" % bar_date)
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, bar_date, symbol, dt, sig_dir, order_price, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'


if __name__ == "__main__":
    path1 = os.path.abspath('.')
    csv_dir = 'data_csv'
    csv_dir = os.path.join(path1,csv_dir)
    symbol_list = ['AAPL']
    # symbol_list = ['hs300']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2015, 5, 1, 0, 0, 0)
    backtest = Backtest(
        csv_dir, symbol_list, initial_capital, heartbeat,
        start_date, HistoricCSVDataHandler, SimulatedExecutionHandler,
        My_portfolio, MovingAverageCrossStrategy
    )
    backtest.run_trading()
