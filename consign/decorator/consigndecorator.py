from functools import wraps
from inspect import isgeneratorfunction

import builtins

from .consigntask import Task
from .consignorder import ConsignOrder


def coroutine(debug: bool = False, *, create_callback=None, complete_callback=None):
    """consign的核心，coroutine使得被修饰函数可以以协程的方式被执行

    他的作用很简单，就是包裹函数，无论是普通函数还是生成器函数，使得consign得以运行他们

    .. seealso::

        普通函数的话， ``coroutine`` 会生成一个包装好的生成器函数替代

        随后如同对待生成器函数一般使用

    ``coroutine`` 修饰时在程序创建之初会创建  ``ConsignOrder`` 并记录在order属性

    在每次调用时创建  ``Task`` ，同时每次调用的返回值被 ``Task`` 替代，你可以从其中获取更多信息

    被 ``coroutine`` 修饰的函数变成协程后，是非阻塞的，状态、返回值等都可以在 ``Task`` 中获取

    ``coroutine`` 支持传入一些参数，其中比较特别是debug参数

        debug参数允许你在不修改代码的情况下，以代码原本的阻塞逻辑运行

    ``coroutine`` 为修饰器而设计，但你也可以把它当作函数使用，但这也会使得 ``ConsignOrder`` 被不停重复创建而效率低下

    yield是 **控制权转移** 的关键 ，consign在单线程下依旧以 **并发** 的形式运行，关键就在于yield。

    被 ``coroutine`` 修饰的函数最好是生成器函数，且 **尽可能的切分函数控制权** 提高控制权转换的频率

    .. tab-set::

        .. tab-item:: 一般

            .. code-block:: python

                def do_something_x():
                    io.sleep(long long time)
                    return something

                @coroutine
                def my_function():
                    a = do_something_1()
                    b = do_something_2()
                    return a, b

        .. tab-item:: 还行

            .. code-block:: python

                def do_something_x():
                    io.sleep(long long time)
                    return something

                @coroutine
                def my_function():
                    a = yield do_something_1()
                    b = yield do_something_2()
                    return a, b

        .. tab-item:: nice！

            .. code-block:: python

                @coroutine
                def do_something_x():
                    yield io.sleep(long long time)
                    return something

                @coroutine
                def my_function():
                    a = yield do_something_1()
                    b = yield do_something_2()
                    wait(a) or chain_reaction(do_something_x)
                    return a, b

    :param bool debug:

        如果为True， ``coroutine`` 允许你在不修改代码的情况下，以代码原本的阻塞逻辑运行

        如果是非生成器函数直接运行并返回结果

        如果是生成器函数会以一个模拟普通函数的函数 :abbr:`代替运行 (阻塞并不断的next)` 并返回结果

    :param function create_callback:

        创建协程函数时执行的回调函数， ``create_callback`` 在协程函数执行前执行

         ``create_callback`` 需要一个参数用于接收此次运行时的  ``Task``

    :param function complete_callback:

        完成协程函数时执行的回调函数， ``complete_callback`` 在协程函数获取到返回值后执行，但此时协程函数状态并非完成

         ``complete_callback`` 需要一个参数用于接收此次运行时的  ``Task``

    :return:
    """

    def decorator(func):
        # 构造时创建
        order = ConsignOrder(func, create_callback=create_callback, complete_callback=complete_callback)

        def _temp_yield_coroutine_func(*args, **kwargs):
            yield ...
            return func(*args, **kwargs)

        # 用于是生成器函数的修饰，同时适配旧版本
        def coroutine_func(*args, **kwargs):
            order.run_area = builtins.DEFAULT_WORK_AREA.get()
            task = Task(order=order)

            _yield_coroutine_func = func if isgeneratorfunction(func) else _temp_yield_coroutine_func

            # generator, receipts = _yield_coroutine_func(*args, **kwargs), task.create_receipts()
            # task.submit((None, generator, receipts))

            task.submit((None, _yield_coroutine_func(*args, **kwargs), task.create_receipts()))

            return task

        def debug_func(*args, **kwargs):
            func_result = func(*args, **kwargs)

            if not isgeneratorfunction(func):
                return func_result

            # 未来可使用iteration context优化
            try:
                result = next(func_result)
                while True:
                    result = func_result.send(result)
            except StopIteration as e:
                return e.value

        if debug is True:
            return wraps(func)(debug_func)

        setattr(coroutine_func, "order", order)

        return wraps(func)(coroutine_func)  # 考虑将if debug 放到这里来

    if callable(debug):
        # 此时修饰器没有被call
        # 所以debug是被修饰函数
        return decorator(debug)

    return decorator
