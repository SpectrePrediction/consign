from functools import wraps
from inspect import isgeneratorfunction

import builtins

from .consigntask import Task
from .consignorder import ConsignOrder


def coroutine(debug: bool = False, *, create_callback=None, complete_callback=None):
    """
    最关键的，协程修饰器
    协程修饰器使得一个函数得以以协程的方式运行
    如果你的函数返回的并不是生成器，那么他会使用一个替代生成器函数，对齐生成器函数继续往下
    生成器函数会被执行部分内容后提交进入所在work area区域的队列中
        如果需要更换work area无需传递任何参数，仅仅使用With WorkArea即可
        被修饰的函数会被添加order属性，记录了自身创建的部分信息
        被修饰的函数返回值会被修改成Task，同时不再阻塞，你可以使用wait或者从task中获取更多信息（返回值，状态等）

    :param debug: 使用debug使得修饰器失效，返回原函数
    :param create_callback: 创建时回调函数，比协程先执行，需要一个参数用于接收task
    :param complete_callback: 完成时回调函数，此时已经获取了协程的返回值，是协程结束后执行，需要一个参数用于接收task
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
