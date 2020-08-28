# -*- coding: utf-8 -*-
#
# backtest.py

from __future__ import print_function

import datetime
import pprint
import queue
import time
from equity_plot import plot_performance


class Backtest(object):
    """
    Back_test class. The main class that capsule every thing
    """

    def __init__(
            self, csv_dir, symbol_list, initial_capital,
            heartbeat, start_date, data_handler_cls,
            execution_handler_cls, portfolio_cls, strategy_cls
    ):
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date

        self.data_handler_cls = data_handler_cls
        self.execution_handler_cls = execution_handler_cls
        self.portfolio_cls = portfolio_cls
        self.strategy_cls = strategy_cls

        self.events = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1
        self._generate_trading_instances()

        # self.strat_params_list=strat_params_list

    def _generate_trading_instances(self):
        """
        Generate all the instances associated with the trading: data handler, strategy  and execution_handler instance
        """
        print(
            "Creating DataHandler,Strategy,Portfolio and ExecutionHandler/n"
        )
        # print("strategy parameter list:%s..." % strategy_params_dict)
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir,
                                                  self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events)  # Create the instance of strategy
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date,
                                            self.initial_capital)  # create instance of portfolio
        self.execution_handler = self.execution_handler_cls(self.events)

    def _run_backtest(self):
        """
        执行回测
        """
        i = 0
        while True:
            i += 1
            print(i)
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()  # Trigger a market event
            else:
                break
            while True:
                try:
                    event = self.events.get(False)  ##Get an event from the Queue
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)  ## Trigger a Signal event #
                            self.portfolio.update_timeindex()
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(
                                event)  # Transfer Signal Event to order Event and trigger an order event
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':  # finish the order by updating the position. This is quite naive, further extention is required.
                            self.fills += 1
                            self.portfolio.update_fill(event)

            time.sleep(self.heartbeat)

    def _output_performance(self):

        self.portfolio.create_equity_curve_dateframe()  # get equity curve object

        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()

        print("Creating equity curve...")
        print(self.portfolio.equity_curve.tail(10))
        pprint.pprint(stats)

        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)
        self.portfolio.equity_curve.to_csv('equity.csv')
        # self.execution_handler.execution_records.set_index('date_time',inplace =True)
        self.execution_handler.execution_records.to_csv('Execution_summary.csv')

    def run_trading(self):
        """
        模拟回测以及输出业绩结果的过程
        """
        self._run_backtest()
        self._output_performance()
        my_plot = plot_performance(self.portfolio.equity_curve,
                                   self.data_handler.symbol_data[self.symbol_list[0]],
                                   self.execution_handler.execution_records )
        my_plot.plot_equity_curve()
        my_plot.plot_stock_curve()
        my_plot.show_all_plot()
        # out=open("opt.csv","w")
        # spl=len(self.strat_params_list)
        # for i,sp in enumerate(self.strat_params_list):
        #     print("Strategy %s out of %s..." %(i+1,spl))
        #     self._generate_trading_instances(sp)
        #     self._run_backtest()
        #     stats=self._output_performance()
        #     pprint.pprint(stats)
        #
        #     tot_ret=float(stats[0][1].replace("%",""))
        #     sharpe=float(stats[1][1])
        #     max_dd=float(stats[2][1].replace("%",""))
        #     dd_dur=int(stats[3][1])
        #
        #     out.write(
        #         "%s,%s,%s,%s,%s,%s,%s\n" %
        #         sp["ols_window"],sp["zscore_high"],sp["zscore_low"],
        #         tot_ret,sharpe,max_dd,dd_dur
        #     )
        # out.close()
