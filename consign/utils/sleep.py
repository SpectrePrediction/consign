from time import monotonic, sleep

from ..decorator import coroutine, repeated_call, chain_reaction


@repeated_call
@chain_reaction
@coroutine
def asleep(secs: float):
    """
    委托sleep与sleep最大的不同是它是不阻塞的
    委托sleep通过不断判断时间以及转移控制权来实现非阻塞

    注意的是：
        1. 委托sleep并不能保证执行顺序（即使是在单/主线程下）
                因为控制权无法保证谁先获取，举例1和2函数抛出了委托sleep，同时sleep 5秒
            在5秒后，无法保证是1先于2获取到执行的控制权

        2. 委托sleep无法保证时间的稳定性、精细的时间控制（尤其是单/主线程下）
                因为sleep在转移控制权的过程中，其余任务还在协程方式执行，你无法保证
            正在执行的任务不是阻塞的，如果存在一个任务是阻塞的，那么他就有可能对委托
            sleep造成阻塞的影响

                举例： 1函数在第一次抛出sleep 5秒，但2函数抛出一个需要阻塞执行7秒的非协程任务
            假设在单/主线程下执行，那么2函数的任务阻塞时间大于>5秒，且没有控制权的转移（非协程）
            因此，1函数无法在sleep 5秒后得到立即执行， 最大的可能是在2函数任务完成的下一刻被继续执行

                举例2：即使2函数单次任务的阻塞时间（或者说执行耗时）小于<5s，例如2函数的任务执行仅
            需要100ms（0.1s），那么就存在可能1函数在sleep了4.95秒的时候（差50ms结束）转移了控制权，导致当2
            被执行结束的时候，1不得不在5.05s(超了50ms)的时候才得以继续
        3. 委托sleep 为方便协程中使用，已经被

    :param secs:
    :return:
    """
    star = monotonic()
    while (monotonic() - star) < secs:
        yield ...
