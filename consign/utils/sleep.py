from time import monotonic

from ..decorator import coroutine, repeated_call, chain_reaction


@repeated_call
@chain_reaction
@coroutine
def asleep(secs: float):
    """协程的sleep函数，休眠一定时间

    ``asleep`` 与 ``sleep`` 不同， ``asleep`` 是非阻塞的、协程的

    ``asleep`` 通过 **不断的切换控制权** 和 **判断时间** 来实现休眠

    .. warning::

        ``asleep``  :abbr:`无法保证执行顺序 (即使是在单/主线程下)`

            因为控制权无法保证谁先获取

            举例1和2函数抛出了委托sleep，同时sleep 5秒

            在5秒后，无法保证是1先于2获取到执行的控制权

        ``asleep`` 休眠的时长是 **不精确的** ，受到当前任务量和阻塞时间的影响

            因为 ``asleep`` 在转移控制权的过程中，队列里依旧存在其余任务

            你无法保证下一个任务是不是阻塞的

            如果存在任务是阻塞的，那么他就有可能对 ``asleep`` 照成影响

        .. tip::

            你可以通过创建 **充足的线程** 以应对这个问题，同时 **尽可能的切分函数控制权** 提高控制权转换的频率

        ----

        例子

            举例： 1函数在第一次抛出 ``asleep`` 5秒，但2函数抛出一个需要 **阻塞执行7秒** 的 **非协程** 任务

            假设在单/主线程下执行

            那么2函数的任务阻塞时间大于>5秒， :abbr:`且没有控制权的转移 (非协程)`

            因而，1函数无法在sleep 5秒后得到立即执行，

    ``asleep`` 为了方便使用，已经被 ``chain_reaction`` 和  ``repeated_call`` 修饰

    二者分别使得 ``asleep`` 以顺序方式执行、 ``asleep`` 以有参的形式可以再被无参调用执行

    :param float secs:
        休眠的秒数

    """
    star = monotonic()
    while (monotonic() - star) < secs:
        yield ...
