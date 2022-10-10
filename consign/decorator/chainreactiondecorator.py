from functools import wraps

from ..worker.iterationcontext import AutoReceipts


def chain_reaction(func):
    """chain_reaction使得嵌套协程函数可以以链式的方式运行.

    .. warning::

        chain_reaction接收的参数func必须是被 ``coroutine`` 修饰的委托函数.

    被 ``chain_reaction`` 修饰的函数会被添加上对应的标记

    他会重新构造一个精心设计的回调函数来完成嵌套协程到外层协程控制权的切换

    ``Worker`` 会通过标记确认一个协程是否是被 ``chain_reaction`` 修饰，随后通过标记传递必须的信息以供回调时使用

    .. seealso::

        之所以会需要标记传递信息，原因在于现在的 ``chain_reaction`` 的主动权在函数手上

        而旧版在Worker手上，相比之下新版更加自由和随心所欲，但旧版方便，却不好控制

    ``chain_reaction`` 是否修饰的区别在于：

    正常的被修饰的协程函数在被yield调用是非阻塞的，直接返回Task类

    被修饰的函数在被yield调用时会等待函数执行完毕，并直接返回值而非Task类

    简单的说，他能让协程函数中的协程函数以普通顺序的方式运行，但同时能够享受控制权切换的效果

    ----

    例子

    .. tab-set::

        .. tab-item:: 使用chain_reaction

            .. code-block:: python

                from consign import coroutine, chain_reaction

                @chain_reaction
                @coroutine
                def get_value():
                    yield ...
                    return 10

                @coroutine
                def my_test():
                    value = yield get_value
                    print(value)
                    # value is 10

                my_test()
                CoroutineWorker().loop_work(forever=True)

        .. tab-item:: 不使用chain_reaction

            .. code-block:: python

                from consign import coroutine

                @coroutine
                def get_value():
                    yield ...
                    return 10

                @coroutine
                def my_test():
                    value = yield get_value
                    print(value)
                    # value is Task类
                    # 并且此时get_value并没完成

                my_test()
                CoroutineWorker().loop_work(forever=True)

    ``chain_reaction`` 是比轮询更优雅的，但并非在所有情况下

    通常而言，如果对时间有更高可控性的可以使用 ``chain_reaction``

    而更高性能还是建议使用 ``wait``

    :param function func:
        必须是被 ``coroutine`` 修饰的委托函数

    :raise AssertionError:
        当传入参数 ``func`` 不是被 ``coroutine`` 修饰的委托函数时抛出
    """

    order = getattr(func, "order", None)
    assert order, "{func_name} 不是被 coroutine 修饰的委托函数".format(func_name=func.__name__)
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

