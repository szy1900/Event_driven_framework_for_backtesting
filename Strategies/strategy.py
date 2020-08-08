from abc import ABCMeta, abstractmethod

try:
    import Queue as queue
except ImportError:
    import queue


class Strategy(object, metaclass=ABCMeta):
    """
    Strategy类是一个抽象类，提供所有后续派生策略处理对象的接口。派生策略类的目标是
    对于给定的代码基于DataHandler对象生成的数据来生成Signal。
    这个类既可以用来处理历史数据，也可以用来处理实际交易数据。只需要将数据存放到
    数据队列当中
    """

    @abstractmethod
    def calculate_signals(self, event):
        """
        提供一种计算信号的机制
        """
        raise NotImplementedError("Should implement calculate_signals()")
