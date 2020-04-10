# -*- coding: utf-8 -*-

# event.py

from __future__ import print_function


class Event(object):
    """
    Event的基类，提供所有后续子类的一个接口，在后续的交易系统中会触发进一步的
    事件。
    """
    pass


class MarketEvent(Event):
    """
    处理接收到新的市场数据的更新
    """

    def __init__(self):
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    处理从Strategy对象发来的信号的事件，信号会被Portfolio对象所接收并且
    根据这个信号来采取行动
    """

    def __init__(self, strategy_id, date_time, symbol, datetime, signal_type, order_price, strength):
        self.strategy_id = strategy_id
        self.date_time = date_time
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength
        self.order_price = order_price


class OrderEvent(Event):
    """
    处理向执行系统提交的订单（Order）信息。这个订单包括一个代码，一个类型
    （市价还是限价），数量以及方向
    """

    def __init__(self, date_time, symbol, order_type, quantity, buy_or_sell, order_price, direction):
        self.date_time = date_time
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.buy_or_sell = buy_or_sell
        self.direction = direction
        self.order_price = order_price
    def print_order(self):
        """
        输出订单中的相关信息
        """
        print(
            "Order:Symbol:%s,Type=%s,Quantity=%s,Direction=%s, Order_price=%s" %
            (self.symbol, self.order_type, self.quantity, self.direction,self.order_price)
        )


class FillEvent(Event):
    """
    封装订单执行这样一种概念，这个概念是由交易所所返回的。存储交易的数量，
    价格。另外，还要存储交易的佣金和手续费。
    在这里不支持一个订单有多个价格。
    """

    def __init__(self, date_time, symbol, quantity, buy_or_sell,
                 fill_cost, commission=None):
        self.type = 'FILL'
        self.date_time = date_time
        self.symbol = symbol
       # self.exchange = exchange
        self.quantity = quantity
        self.buy_or_sell = buy_or_sell
        self.fill_cost = fill_cost

        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        """
        用来计算基于Interactive Brokers的交易费用。
        """
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost
