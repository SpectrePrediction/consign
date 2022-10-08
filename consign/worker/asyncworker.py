# import threading
# dummy相当于threading的封装，他能很好的修改成多进程支持，方便在io密集和cpu密集中做出取舍
# 但值得一提的是，目前不支持多进程，因为修饰器的关系（work_area被修饰)，将在下版本更新
from multiprocessing.dummy import Process, current_process
from uuid import uuid4
from itertools import repeat

from .coroutineworker import CoroutineWorker


class AsyncWorker(CoroutineWorker):
    """AsyncWorker异步协程Worker，AsyncWorker能够创建线程以应对耗时的阻塞IO，基于CoroutineWorker

    ``AsyncWorker`` 可以将 :abbr:`耗时的事情 (任意阻塞函数)` 分配给许多线程去处理，得以实现异步

    .. seealso::

        当然，如果你使用 ``chain_reaction`` ，那么他依旧还是顺序执行的

        所以如果性能有更高要求，建议灵活使用 ``wait``

    ``AsyncWorker`` 的使用方法通常是 ``init_thread`` 创建线程，很少且不建议使用 ``loop_work``

    如果你使用 ``AsyncWorker`` ，那么 ``loop_work(forever=False)``  **在切换很快时是不可信的**

    :abbr:`这是由于队列qsize不确定性 (官方的描述:由于多线程或者多进程的上下文，这个数字是不可靠的。请注意，这可能会在Unix平台上引起 NotImplementedError)` 以及框架的获取提交导致的

    .. tip::

       通常在多线程下使用 ``loop_work(forever=True)`` 或者重复 ``while True`` 使用 ``loop_work(forever=False)``

    loop_work会把当前线程 **阻塞** 并作为一个 **临时的worker** 去工作

    所以如果 ``AsyncWorker`` 不使用 ``init_thread`` 直接使用 ``loop_work`` 其实和 ``CoroutineWorker`` 效果是 **相同的**

    都是使用 **当前进程** 去工作，是 **单线程** 的，所以任何阻塞的函数都会导致阻塞。

    ``AsyncWorker`` 创建的线程默认是 **守护线程** ，如果你的程序没有阻塞一路到exit的话，可能导致协程任务异常被终止

    所以在 **非cmd** 下，最好使用 ``while True`` 或者 ``loop_work(forever=True)`` 去阻塞，或者设置参数选择生成非守护线程。

    ----

    例子

    .. code-block:: python

        some_coroutine()

        aw = AsyncWorker()
        using_thread_num = 5
        # name_iter 传入为None的时候，默认使用uuid去生成名字
        aw.init_thread(using_thread_num, name_iter=(f"DEFAULT_WORK_AREA_{i}" for i in range(using_thread_num)))

        # 如果程序主进程没有其他内容，那么需要你使用阻塞，可以使用while或者Worker的loop_work
        some_loop()

    :param str work_area_name:

        ``WorkArea`` 的名字，``AsyncWorker`` 会通过名字获取对应的 ``WorkArea``

    :param WorkArea work_area:

        work_area是显式参数，需要显式调用

        可以直接指定 ``WorkArea`` ，如果直接指定，会跳过 ``work_area_name`` 的查找过程

    :raise AssertionError:
        当传入参数 ``work_area_name`` 无法被找到时抛出

    """

    def __init__(self, work_area_name: str = "DEFAULT_WORK_AREA", *, work_area=None):
        super(AsyncWorker, self).__init__(work_area_name, work_area=work_area)
        self.show_str = f"<AsyncWorker at {hex(id(self))} work in {self.work_area}>"
        # __thread_list不对外暴露，对外建议使用thread_list
        self.__thread_list = []

    @property
    def thread_list(self)->list:
        """
        在获取thread_list时，同时检测并删除__thread_list中已经关闭的线程

        .. warning::

            注意这个处理会同步修改到__thread_list

            返回的List并不是副本而是某种'引用'

        :return: 存放线程的列表
        """
        # 在获取thread_list时，同时检测并删除__thread_list中已经关闭的线程
        self.clear_dead_thread()
        # 返回处理后的情况，注意这个处理会同步修改到__thread_list，所以返回的并不是副本，请不要滥用
        return self.__thread_list

    def clear_dead_thread(self):
        """
        一般不建议外部调用

        遍历列表并判断线程是否存活

        如果线程不存活，那么从列表中删除此线程

        :return: None
        """
        [self.__thread_list.remove(thread) for thread in self.__thread_list if not thread.is_alive()]

    def create_thread(self, name=None, daemon=True):
        """
        创建一个持续运行的线程，用于对协程函数进行执行

        :param str name:

            创建的线程名， 如果为None，则使用uuid创建

        :param bool daemon: 是否守护线程

        :return: 创建的线程对象
        """
        # consign_thread = threading.Thread(target=self.loop_work, name=f"consign_{name or uuid4()}")
        consign_thread = Process(target=self.loop_work, name=f"consign_{name or uuid4()}")
        self.__thread_list.append(consign_thread)
        consign_thread.daemon = daemon
        consign_thread.start()
        return consign_thread

    def init_thread(self, create_num, name_iter=None, daemon=True):
        """
        可以一次初始化多个线程

        是对 ``create_thread`` 的上层封装

        :param int create_num: 创建对应线程的数量

        :param name_iter:

            生成器或者容器，如果没有默认使用传递 None 即使用uuid命名

            .. warning::

                没有对 ``name_iter`` 长度做校验
                但 ``name_iter`` 长度应该跟create_num相同，避免出乎意料的结果

        :param bool daemon: 创建的是否是守护线程

        :return:
        """
        tuple(map(self.create_thread, name_iter or repeat(None, create_num), repeat(daemon, create_num)))

    def submit_thread_stop_flag(self):
        """
        向对应 ``WorkArea`` 提交约定的结束信号

        .. warning::

            约定的结束信号不一定能立马结束，因为队列中可能还有其他内容

        :return:
        """
        # 提交约定的结束信号，但注意，约定的结束信号不一定能立马结束，因为队列中可能还有其他内容
        # 同时可能被其他Worker接收，比如协程Worker，所以复杂情况下结果并不确定
        self.submit_work(None, None, None)

