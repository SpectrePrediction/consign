from functools import wraps


def repeated_call(debug):
    """
    他的本质只是将一个函数被修饰成闭包
    eg：
        def test(1) -> def test(1)()
        def test(1,2,3) -> def test(1,2,3)()

    但他不是必须修饰的！因为Worker只在乎你yield的是否是一个无参的可调用对象，如果你本身是无参的，可以直接传递函数名
    如果你不使用他，那么函数将会在yield前被调用，yield的是一个返回值
    如果你使用他修饰了，那么你看似调用了函数，但其实本质是获得了一个中间函数

    :param debug:
    :return:
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
