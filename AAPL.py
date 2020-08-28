# -*- coding: utf-8 -*-

# mac.py
from __future__ import print_function

import datetime
import math
import os
from event import OrderEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio
from Strategies.MovingAverageCrossStrategy import MovingAverageCrossStrategy
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

if __name__ == "__main__":
    print('text')
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
        start_date, data_handler_cls=HistoricCSVDataHandler, execution_handler_cls=SimulatedExecutionHandler,
        portfolio_cls=My_portfolio, strategy_cls=MovingAverageCrossStrategy
    )
    backtest.run_trading()
