...


def except_and_pass_func(*args, **kwargs):
    # 用于捕获异常后什么事都没发生的函数
    return True


class AutoCallback(object):

    def __init__(self, callback, exceptions):
        """
        AutoCallback 是一个上下文类，同时是一个基类，他的作用是:
            当遇到 exceptions参数传入的异常类型时，调用 callback传入的回调
            注意： callback回调应当与__exit__的参数相同：exc_type, exc_val, exc_tb

        :param callback: 回调函数，需要参数 exc_type, exc_val, exc_tb, 如果为None，默认使用 except_and_pass_func
            tips: 如果你希望 AutoCallback 上下文不抛出异常，你需要在 callback 中 return True
        :param exceptions: 异常类型 或者 容器（异常类型1， 异常类型2...)
        """
        self.callback = callback or except_and_pass_func
        self.exceptions = exceptions

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, self.exceptions):
            return self.callback(exc_type, exc_val, exc_tb)


class NoChainReactionError(Exception):
    # 他是链式反应的提示错误
    pass


class CheckChainReaction(AutoCallback):

    def __init__(self, result):
        """
        链式反应检测上下文管理器
        他的思想很简单，就是如果不符合链式反应发生的条件，那么抛出NoChainReactionError
        当自身接收到NoChainReactionError错误时，跳过后续的代码，退出上下文
        如果没接收到NoChainReactionError错误，那么继续向下执行
        :param result:
        """
        super(CheckChainReaction, self).__init__(callback=None, exceptions=NoChainReactionError)
        self.result = result
        self.chain_reaction_flag = getattr(getattr(self.result, "order", False), "chain_reaction_flag", False) is True

    def raise_error_func(self, *args, **kwargs):
        raise NoChainReactionError

    def set_chain_reaction(self, parent_generator, parent_receipts):
        # 获取order是避免每次都通过result去获取order，聊胜于无吧
        order = self.result.order
        # 如果符合要求，那么按约定提供他的父类的生成器和回执以供他回调时用到，他指的是链式反应标注携带者
        setattr(self.result, "_chain_reaction", (parent_generator, parent_receipts))
        # 设置flag为False和还原complete_callback
        # 这是因为chain_reaction现在更加的自由，他可能不知是修饰器，也可能函数调用
        # 如果是修饰器，被修饰的函数其实永远会链式反应，下面的步骤不是必须的
        # 但如果函数调用，那么我们应当只需要此次执行链式反应，而下次依旧原样，所以有此代码
        order.chain_reaction_flag = False
        order.complete_callback = order.old_complete_callback
        # 象征意义的返回，事实上你返回任意值只有在是链式反应时才有作用
        return True

    def __enter__(self):
        # 进入时根据是否有链式反应发生的条件返回不同的函数（是否携带flag且为True，
        return self.set_chain_reaction if self.chain_reaction_flag else self.raise_error_func


class AutoClosing(AutoCallback):

    def __init__(self, thing, exceptions=StopIteration):
        """
        AutoClosing 是一个上下文类，他的作用是：
            遇到 exceptions参数传入的异常类型时
        :param thing:
        :param exceptions: 异常类型 或者 容器（异常类型1， 异常类型2...)
        """
        self.thing = thing
        super(AutoClosing, self).__init__(callback=self.thing_close, exceptions=exceptions)

    def thing_close(self, exc_type, exc_val, exc_tb):
        self.thing.close()
        return True

    def __enter__(self):
        return self.thing


class AutoReceipts(AutoCallback):

    def __init__(self, receipts):
        """
        AutoReceipts 是一个上下文类，他的作用是：
            遇到 StopIteration 时，自动调用 receipts.send(value) 其中的 value 是 exc_val.value
            并且关闭 receipts -> 调用 receipts.close()
            tips: 使用 AutoReceipts 能够获得相比于原版代码更好的代码可读性
        :param receipts: 通过Task类创建的单次调用回执
        """
        self.receipts = receipts
        super(AutoReceipts, self).__init__(callback=self.send_receipts, exceptions=StopIteration)

    def send_receipts(self, exc_type, exc_val, exc_tb):
        receipts = self.receipts

        with AutoClosing(receipts, StopIteration):
            # 由于receipts是约定好的，所以理论上只有一次yield
            # 当receipts触发StopIteration时，AutoClosing会自动捕获异常并关闭receipts
            receipts.send(exc_val.value)

        return True

