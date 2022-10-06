import builtins


class ConsignOrder(object):
    def __init__(self, consignor_func, create_callback=None, complete_callback=None):
        """
        协程订单类型
        他的作用是记录协程的部分信息，他在修饰器创建时就被定义（而非运行调用时）
        他影响着例如回调callback函数的定义，以及用于一些特殊的标记，同样的，他也是判断是否是协程函数的关键

        :param consignor_func: 被修饰函数的原函数
        :param create_callback: 是最先运行的自定义函数
        自定义函数应当满足以下条件：
            1.必须有一个参数位
                这个参数位用于传入清单本身（self)

        :param complete_callback: 是最后运行的自定义函数
        自定义函数应当满足以下条件：
            1.必须有一个参数位
                这个参数位用于传入清单本身（self)
        当这个函数被调用时，说明清单已经更新并且协程已经结束
        """
        self.consignor_func = consignor_func
        self.complete_callback = complete_callback
        self.create_callback = create_callback
        self.create_area = builtins.DEFAULT_WORK_AREA.get()
        self.chain_reaction_flag = False

    def all_info(self):
        # 未来抽象出一个类，用于自动获取成员和对应的值
        return {
            "consignor_func": self.consignor_func,
            "create_area": self.create_area,
            "create_callback": self.create_callback,
            "complete_callback": self.complete_callback,
        }

    def __str__(self):
        return str(self.all_info())

    __repr__ = __str__
