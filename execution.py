# -*- coding: utf-8 -*-

# execution.py

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import pandas as pd

try:
    import Queue as queue
except ImportError:
    import queue

from event import FillEvent


class ExecutionHandler(object, metaclass=ABCMeta):
    """
    ExecutionHandler抽象类处理由Portfolio生成的order对象与实际市场中发生的
    Fill对象之间的交互。
    这个类可以用于实际的成交，或者模拟的成交
    """

    @abstractmethod
    def execute_order(self, event):
        """
        获取一个Order事件并执行，产生Fill事件放到事件队列中
        """
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    这是一个模拟的执行处理，简单的将所有的订单对象转化为等价的成交对象，不考虑
    时延，滑价以及成交比率的影响。
    """

    def __init__(self, events):
        self.events = events
        self.execution_records = pd.DataFrame(columns=['date_time', 'symbol', 'direction', 'quantity', 'order_price',
                                                       'return_profit', 'return_profit_pct' ])
        self.recent_deal_average_cost = 0
        self.entry_time = 0
    def execute_order(self, event):
        """
        Generate the order event and make the execution log
        """
        if event.type == 'ORDER':
            fill_event = FillEvent(event.date_time,
                                   event.symbol,
                                   event.quantity, event.buy_or_sell, fill_cost=None, commission=None)
            self.events.put(fill_event)
            if event.direction != 'EXIT':
                self.entry_time += 1
                self.execution_records = self.execution_records.append(
                    pd.DataFrame(
                        {'date_time': [event.date_time],'symbol': [event.symbol],'direction': [event.direction],
                         'quantity': [event.quantity], 'order_price': [event.order_price],
                         'return_profit': None, 'return_profit_pct': None}))
                self.recent_deal_average_cost = self.recent_deal_average_cost*(self.entry_time-1)/(self.entry_time) + event.order_price/(self.entry_time)
            else:
                return_profit = (event.order_price - self.recent_deal_average_cost)*event.quantity
                return_profit_pct = (event.order_price - self.recent_deal_average_cost)/self.recent_deal_average_cost
                self.execution_records = self.execution_records.append(
                    pd.DataFrame(
                        {'date_time': [event.date_time], 'symbol': [event.symbol], 'direction': [event.direction],
                         'quantity': [event.quantity], 'order_price': [event.order_price],'return_profit': return_profit,
                         'return_profit_pct': return_profit_pct }))
                self.recent_deal_average_cost = 0
                self.entry_time = 0


