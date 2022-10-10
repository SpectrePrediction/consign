from .iterationcontext import AutoReceipts, AutoCallback, CheckChainReaction

from queue import Empty
import builtins


class CoroutineWorker(object):
    """CoroutineWorker协程Worker，CoroutineWorker能够以并发的方式执行特定的协程函数，是所有Worker的基石

    ``CoroutineWorker`` 可以将 :abbr:`控制权切换以实现并发的效果 (通过yield实现控制权切换)`

    ``CoroutineWorker`` 的使用方法通常是 ``loop_work`` 阻塞并完成当前队列中的全部内容

    如果你使用 ``CoroutineWorker`` 在多线程/进程环境下，那么 ``loop_work(forever=False)``  **在切换很快时是不可信的**

    :abbr:`这是由于队列qsize不确定性 (官方的描述:由于多线程或者多进程的上下文，这个数字是不可靠的。请注意，这可能会在Unix平台上引起 NotImplementedError)` 以及框架的获取提交导致的

    .. tip::

       通常在多线程下使用 ``loop_work(forever=True)`` 或者重复 ``while True`` 使用 ``loop_work(forever=False)``

    loop_work会把当前线程 **阻塞** 并作为一个 **临时的worker** 去工作

    使用的是 **当前进程** 去工作，是 **单线程** 的，所以任何阻塞的函数都会导致阻塞。

    ----

    例子

    .. code-block:: python

        some_coroutine()

        cw = CoroutineWorker()
        cw.loop_work()

    :param str work_area_name:

        ``WorkArea`` 的名字，``CoroutineWorker`` 会通过名字获取对应的 ``WorkArea``

    :param WorkArea work_area:

        work_area是显式参数，需要显式调用

        可以直接指定 ``WorkArea`` ，如果直接指定，会跳过 ``work_area_name`` 的查找过程

    :raise AssertionError:
        当传入参数 ``work_area_name`` 无法被找到时抛出

    """

    def __init__(self, work_area_name: str="DEFAULT_WORK_AREA", *, work_area=None):
        #: ``CoroutineWorker`` 为此 ``WorkArea`` 工作
        self.work_area = work_area or getattr(builtins, "WORK_AREA_DICT", {}).get(work_area_name, None)
        assert self.work_area, "WORK_AREA_DICT不存在 或 WORK_AREA_DICT中没有名为 {work_area_name} 的key".format(
            work_area_name=work_area_name)

        self.show_str = "<CoroutineWork at {work_id} work in {work_area}>".format(
            work_id=hex(id(self)), work_area=self.work_area)

    def qsize(self):
        """
        获得 ``WorkArea`` 队列中的大概数量

        .. warning::

            由于多线程或者多进程的上下文，这个数字是不可靠的。

            请注意，这可能会在Unix平台上引起 NotImplementedError ，如 macOS ，因为其上没有实现 sem_getvalue() 。

        :return:

            获得 ``WorkArea`` 队列中的大概数量

        :raise NotImplementedError:

            能会在Unix平台上引起 NotImplementedError ，如 macOS ，因为其上没有实现 sem_getvalue()

        """
        return self.work_area.queue.qsize()

    def submit_work(self, *args):
        """
        提交任务到 ``WorkArea`` 队列

        不建议外部调用， 如果调用需要明白自己正在做什么

        :param args:

            按照规定 ``WorkArea`` 队列中是只应当put一个定义好的tuple

            其格式为(yield_value, generator, receipts)

            这里因为不向外调用，所以使用可变参偷了个懒，就无需再手动创建tuple

        :return: None

        :raise Full:

            当 ``WorkArea`` 队列存放满时触发

        """
        self.work_area.queue.put(args)
        # 为什么改用上面这个？
        # 因为我发现其实submit_work不应该给用户调用，即使是外部也是自己明白需要做什么而调用
        # 那么通过args，直接转换成tuple，偷个懒
        # 原来的代码：
        # self.work_area.queue.put((yield_value, generator, receipts))

    def work_once(self, time_out=None):
        """
        ``CoroutineWorker`` 获取一次 ``WorkArea`` 队列中的内容并执行一次

        任意一种情况返回都会视作一次Work

        :param time_out:

            等待 ``WorkArea``  队列获取内容的等待超时时长

        :return:

            返回bool类型

            False 意味着收到了约定的结束信号

            True 表示正常结束Work

        :raise Empty:

            当 ``WorkArea`` 队列为空时阻塞时长超过参数 ``time_out`` 时抛出

        :raise ValueError:

            当参数 ``time_out`` 不正确时抛出

        """
        # yield_value是由yield传递出来的值, 尽可能的是一个callable
        #   新版和旧版的区别在于：不在要求一定是一个callable，如果callable，那么调用，否则原样返回
        # generator是返回的生成器，用于send和执行下一步并得到yield_value
        # receipts是定义好的回执函数，一个特殊的generator, 用于触发两次回调和获取函数的最终结果
        yield_value, generator, receipts = self.work_area.queue.get(timeout=time_out)

        if generator is None or receipts is None:
            # 约定的停止信号
            return False

        if yield_value is None and generator.gi_frame.f_lasti == -1:
            # 表明此generator还未开始迭代, 进行初始化(此处是适配旧版）
            _, yield_value = next(receipts), next(generator)
            # 选择提交而不是继续执行的原因是希望这样可以更快的轮询queue
            self.submit_work(yield_value, generator, receipts)
            return True

        # 新版本不再需要链式反应，或者说链式反应将会显著的、手动的启用
        # 链式反应是比主动轮询+补偿工作更好的设计
        #   主动轮询+补偿工作是提交一个轮询任务（循环判断是否完成）并将自身作为补偿的工作者进行工作并阻塞，等待结果
        #       直到轮询任务得到的结果是满意的结果，工作者结束工作，主动轮询并不精确，但补偿工作使得线程资源不会浪费
        #   而链式反应更胜一筹，因为链式反应的存在必须是一个嵌套yield的情况，所以链式反应可以先暂停父生成器的执行，转而
        #       执行子生成器，当子生成器完成时，通过将父生成器重新提交进入队列来重启父生成器，更加的高效

        # 新版本同样不再强调yield_value是一个callable，但如果他是，它会被调用
        result = yield_value() if callable(yield_value) else yield_value

        with CheckChainReaction(result) as try_set_chain_reaction:
            is_chain_reaction = try_set_chain_reaction(generator, receipts)
            # 如果不是链式反应，通过抛出自定义异常, 被CheckChainReaction捕获同时跳过return
            if is_chain_reaction:
                # 其实在逻辑上，这个if是没有意义的，因为不是chain_reaction通过触发异常跳过return
                # 但这样写编辑器不会报警告，我以为会很简洁，是我考虑不周了
                return True

        with AutoReceipts(receipts):
            yield_value = generator.send(result)
            # 倘若 generator.send 触发了 StopIteration, AutoReceipts会捕获异常、执行receipts且不会往下执行submit_work
            self.submit_work(yield_value, generator, receipts)

        return True

    def loop_work(self, *, time_out=0.1, forever=True):
        """

        ``loop_work`` 阻塞并完成当前队列中的全部内容 或者 收到停止信号

        .. warning::

            在多线程/进程环境下

            forever参数为False时需要考虑 :abbr:`队列qsize的不确定性 (由于多线程或者多进程的上下文，这个数字是不可靠的。)`

            .. tip::

                通常在多线程下使用 ``loop_work(forever=True)`` 或者重复 ``while True`` 使用 ``loop_work(forever=False)``

        :param time_out:

            等待 ``WorkArea``  队列获取内容的等待超时时长

        :param forever:

            是否永久阻塞

            如果 ``forever`` 为False，那么 ``loop_work`` 会考虑队列的 ``qsize`` 是否<=0

            如果队列的 ``qsize`` <=0，那么退出循环

            如果你需要指定某个任务完成并阻塞，那么建议使用 ``wait`` 来确保完成优于直接使用 ``forever`` =True

        :return: None

        :raise ValueError:

            当参数 ``time_out`` 不正确时抛出

        """
        flag = True
        while flag:
            # AutoCallback用于捕获异常，callback为None，默认不做处理
            with AutoCallback(None, (Empty, StopIteration)):
                # 当work_once返回false，说明要结束loop_work了
                flag = self.work_once(time_out)

            flag = flag and (forever or self.qsize() > 0)

    def __str__(self):
        return self.show_str

    __repr__ = __str__
