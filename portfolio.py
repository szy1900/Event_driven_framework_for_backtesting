# -*- coding: utf-8 -*-

# portfolio.py
try:
    import Queue as queue
except ImportError:
    import queue

import pandas as pd
from abc import abstractmethod
from performance import create_sharpe_ratio, create_drawdowns


class Portfolio(object):
    """
    Portfolio类处理所有的持仓和市场价值，针对在每个时间点上的数据的情况
    postion DataFrame存放一个用时间做索引的持仓数量
    holdings DataFrame存放特定时间索引对应的每个代码的现金和总的市场持仓价值，
    以及资产组合总量的百分比变化。
    """

    def __init__(self, bars, events, start_date, initial_capital=100000):
        self.bars = bars
        self.events = events

        self.symbol_list = self.bars.symbol_list
        self.latest_datetime = None

        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.__construct_all_positions()

        self.current_positions = dict((k, v) for k, v in \
                                      [(s, 0) for s in self.symbol_list])

        self.all_holdings = self.__construct_all_holdings()
        self.current_holdings = self.__construct_current_holdings()


    def __construct_all_positions(self):
        """
        使用start_date来确定时间索引开始的日期来构造所有的持仓列表
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]

    def __construct_all_holdings(self):
        """
        这个函数构造一个字典，保存所有的代码的资产组合的startdate的价值
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def __construct_current_holdings(self):
        """
        这个函数构造一个字典，保存所有代码的资产组合的当前价值
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self):  # sumarize the hoilding information. Just for recording
        """
        在持仓矩阵当中根据当前市场数据来增加一条新纪录，它反映了这个阶段所有持仓的市场价值
        """
        self.latest_datetime = self.bars.get_latest_bar_datetime(
            self.symbol_list[0]
        )
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = self.latest_datetime
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        self.all_positions.append(dp)

        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = self.latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            market_value = self.current_positions[s] * \
                           self.bars.get_latest_bar_value(s, "adj_close")
            dh[s] = market_value
            dh['total'] += market_value
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill_event):
        """
        获取一个Fill对象并更新持仓矩阵来反映最新的持仓
        """
        fill_dir = 0
        if fill_event.buy_or_sell == 'BUY':
            fill_dir = 1
        if fill_event.buy_or_sell == 'SELL':
            fill_dir = -1
        self.current_positions[fill_event.symbol] += fill_dir * fill_event.quantity

    def update_holdings_from_fill(self, fill):
        """
        获取一个Fill对象并更新持仓价值矩阵来反映持仓市值
        """
        fill_dir = 0
        if fill.buy_or_sell == 'BUY':
            fill_dir = 1
        if fill.buy_or_sell == 'SELL':
            fill_dir = -1

        fill_cost = self.bars.get_latest_bar_value(
            fill.symbol, "adj_close"
        )
        cost = fill_dir * fill_cost * fill.quantity;
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        # self.current_holdings['total']=self.current_holdings['total'] - fill.commission
        a = 1

    def update_fill(self, event):
        """
        在接收到FillEvent之后更新当前持仓和市值
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    @abstractmethod
    def generate_naive_order(self, signal):
        raise NotImplementedError("Should implement generate_naive_order()")

    # def generate_naive_order(self,signal):
    #     """
    #     简单的生成一个订单对象，固定的数量，利用信号对象，没有风险管理
    #     或头寸调整的考虑
    #     """
    #     order=None
    #
    #     symbol=signal.symbol
    #     direction=signal.signal_type
    #     strength=signal.strength
    #
    #     mkt_quantity=100
    #     cur_quantity=self.current_positions[symbol]
    #     order_type='MKT'
    #
    #     if direction=='LONG' and cur_quantity==0:
    #         order=OrderEvent(symbol,order_type,mkt_quantity,'BUY')
    #     if direction=='SHORT' and cur_quantity==0:
    #         order=OrderEvent(symbol,order_type,mkt_quantity,'SELL')
    #     if direction=='EXIT' and cur_quantity>0:
    #         order=OrderEvent(symbol,order_type,abs(cur_quantity),'SELL')
    #     if direction=='EXIT' and cur_quantity<0:
    #         order=OrderEvent(symbol,order_type,abs(cur_quantity),'BUY')
    #
    #     return order
    def update_signal(self, event):
        """
        基于SignalEvent来生成新的订单，完成Portfolio的逻辑
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def create_equity_curve_dateframe(self):
        """
        基于all_holdings创建一个pandas的DataFrame。
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
        """
        Equity_summary
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100)),
                 ("Drawdown Duration", "%d" % dd_duration)]
        self.equity_curve.to_csv('equity.csv')
        return stats
