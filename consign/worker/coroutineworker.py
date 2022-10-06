from .iterationcontext import AutoReceipts, AutoCallback, CheckChainReaction

from queue import Empty
import builtins


class CoroutineWorker(object):

    def __init__(self, work_area_name: str="DEFAULT_WORK_AREA", *, work_area=None):
        """
        协程Worker，现在的他是所有Worker的底层，更多的Worker不是继承就是组合他
        协程Worker会负责一个work area的队列，处理队列中的任务，他本质是单线程的
        通过控制权专业实现来回切换的效果，模拟并发，举个例子：
            如果你使用time.sleep 1（其模拟一个阻塞的任务），那么单线程下的协程Worker同时会阻塞 1 秒再执行下一段
            但如果你使用此库自带的 asleep 1 (模拟协程任务)，那么单线程下你也能发现，可以实现类似并发的效果，因为asleep是
                非阻塞的
        :param work_area_name: work_area名字，默认 默认work_area，会通过名字获取work_area，如果没找到，抛出异常
        :param work_area: 直接指定work_area，如果直接指定，会跳过work_area_name的查找过程
        :raise: AssertionError
        """
        self.work_area = work_area or getattr(builtins, "WORK_AREA_DICT", {}).get(work_area_name, None)
        assert self.work_area, f"WORK_AREA_DICT不存在 或 WORK_AREA_DICT中没有名为'{work_area_name}'的key"

        self.show_str = f"<CoroutineWork at {hex(id(self))} work in {self.work_area}>"

    def qsize(self):
        """
        队列中的大概数量
        可用于判断当前队列中是否还有未启动的协程
        注意：这只是获取大概数量，官方有说，他是不准确的，具体如下：
            由于多线程或者多进程的上下文，这个数字是不可靠的。
            请注意，这可能会在Unix平台上引起 NotImplementedError ，如 macOS ，因为其上没有实现 sem_getvalue() 。
        :return:
        :raise: NotImplementedError
        """
        return self.work_area.queue.qsize()

    def submit_work(self, *args):
        """
        提交给队列
        :param args:
        :return:
        :raise: Full (put触发)
        """
        self.work_area.queue.put(args)
        # 为什么改用上面这个？因为我发现其实submit_work不应该给用户调用，即使是外部也是自己明白需要做什么而调用
        # 那么通过args，直接转换成tuple，偷个懒
        # self.work_area.queue.put((get, generator, receipts))

    def work_once(self, time_out=None):
        """
        工作一次
        :param time_out:get的wait时长
        :return: bool False意味着收到了约定的结束信号，True表示正常结束
        :raise: Empty、ValueError(Queue get引发)
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
            _, yield_value = receipts.__next__(), generator.__next__()
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
        阻塞并工作直到某种条件达成或者收到停止信号

        :param time_out: 单次work_once的等待时间，也是当队列为空时的轮询时间
        :param forever: 是否永久阻塞，如果非永久，那么loop_work会考虑队列的qsize是否<=0
            如果<=0那说明队列中内容被执行完毕了，那么退出循环

            多线程下(AsyncWorker)需要注意：
                forever=False不建议使用在多线程环境中，如果使用，你需要考虑loop_work退出后线程的情况
                    因为在多线程中，qsize是不确定的，所以可能超出你的预期

                同样在多线程下，forever=False也需要注意，由于此框架的特殊性（获取-执行-提交）和qsize的不确定性，可能出现
                    获取后执行时，新的任务还未提交(获取qsize的时候，另一个线程get取走了最后的单个任务)，此时获取qsize可
                    能为0，导致loop work退出，任何单独的任务都有可能导致这个情况发生，所以forever=False是不可信的。如果
                    你需要指定某个任务完成并阻塞，那么建议使用wait

        :return:
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
