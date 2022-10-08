from functools import wraps


def repeated_call(debug):
    """repeated_call函数/修饰器可以将一个函数修饰成闭包，使得函数以有参形式调用后可以再一次被无参调用

    .. code-block:: python

        def test(something: any):
            return something

        test("hi")

    当其被修饰时，相当于

    .. code-block:: python

        @repeated_call
        def test(something: any):
            return something

        # 此时返回的是一个替代函数，test并没有被真正执行
        test("hi")
        # 完整的执行过程，等价于没修饰前的test("hi")
        test("hi")()

    ``repeated_call`` 并不是必须的，与之相似功能的还有 functools中的 ``partial`` 以及 class中的 ``__call__`` 方法

    .. warning::

        一般而言，他的使用是为了consign中的一项规则：yield 一个 function 时，function 应当满足无参的条件

        但值得注意的是，这个条件可能在 **未来被移除** ，有违简单易用这个初衷，他是我为了自己旧版项目做的兼容


    ``repeated_call`` 并不是必须的！因为consign只在乎你yield的是否是一个无参的可调用对象
    如果你本身是无参的，可以直接传递函数名

    通常情况下，你可以直接在yield前调用function， **这其实意味着你yield的是调用函数后的返回值** 。

    :param bool debug:
        如果为True，那么返回原函数

    :raise AssertionError:
        当传入参数 ``func`` 不是 ``callable`` 时抛出

    """
    def decorator(func):

        if debug is True:
            return func

        assert callable(func), f"{func} 不是一个可调用对象"

        def _temp_func(*args, **kwargs):
            def _recall_func():
                return func(*args, **kwargs)

            return wraps(func)(_recall_func)

        return wraps(func)(_temp_func)

    if callable(debug):
        return decorator(debug)

    return decorator
