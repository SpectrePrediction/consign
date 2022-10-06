from functools import wraps

from ..worker.iterationcontext import AutoReceipts


def chain_reaction(func):
    """
    链式反应函数 支持修饰器用法
    相较于以往通过传参给Worker在进行时进行链式反应而言，重构后的consign需求更显式的调用链式反应：
        现在的chain_reaction更加自由，允许在同一个协程函数中，只启动部分函数链式反应
        同样兼容旧版，允许修饰器用法，被修饰函数意味着当其出现在任意协程内，都会以链式反应触发
        相较于旧版，链式反应不再依赖Worker是否启动处理链式反应，而是将主动权给到函数上，被修饰或者调用的函数将会链式

    链式反应是否启动区别在于，正常的被修饰的协程函数调用是非阻塞的，直接返回Task类，你可以通过许多方法去阻塞他
        但一旦启动了链式反应，当一个启动链式反应的协程函数（子协程）运行在另一个被修饰的协程函数（父协程）中，
            将会阻塞子协程函数，直到子协程函数结束，再次启动父协程函数，同时返回的是子协程的返回值而不是task
        简单的说，他能让协程函数中的协程函数以普通顺序的方式运行，但同时能够享受控制权切换的效果

    :param func:
    :return:
    """

    order = getattr(func, "order", None)
    assert order, f"{func.__name__} 不是被 coroutine 修饰的委托函数"
    default = (None, None)
    order.old_complete_callback = old_complete_callback = order.complete_callback

    def chain_reaction_callback(task):
        generator, receipts = getattr(task, "_chain_reaction", default)

        if generator is not None and receipts is not None:
            setattr(task, "_chain_reaction", default)
            with AutoReceipts(receipts):
                yield_value = generator.send(task.value)
                task.submit((yield_value, generator, receipts))

        if old_complete_callback is not None:
            old_complete_callback(task)

    @wraps(func)
    def decorator(*args, **kwargs):
        order.chain_reaction_flag = True
        order.complete_callback = chain_reaction_callback

        return func(*args, **kwargs)

    return decorator

