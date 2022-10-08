from queue import Empty

from ..decorator.consigntask import Task, TaskResult, TaskState
from ..decorator.consigndecorator import coroutine
from .coroutineworker import CoroutineWorker
from .iterationcontext import AutoCallback
from ..workarea import WorkArea


def pass_func():
    # 后期考虑添加其他逻辑，帮助其他任务等
    pass


class Supervisor:
    """
    ``wait`` 的底层实现

    ``wait`` 是 ``Supervisor`` 类的上层封装， ``wait``  向外暴露，但 ``Supervisor`` 不被直接暴露

    ``Supervisor`` 能够阻塞等待一个 ``Task`` 任务完成，并在期间参与工作

    ``Supervisor``  的原理是： ``Supervisor`` 向此 ``Task`` 类中的 ``WorkArea`` 提交 一个 *轮询* 任务

    *轮询* 任务的作用就是每次执行控制权切换前判断 ``Task`` 的状态是否是已完成

    当 ``Supervisor`` 在接收到 ``Task`` 完成信号后，会在执行完当前手头内容后退出阻塞并返回返回值

    更多详情请查看 wait 函数

    :param Task task:

        需要等待的 ``Task`` 类, 如果传入的对象并非 ``Task`` 类，原样返回

    """

    def __init__(self, task):
        self.task = task
        self.wait_flag = True
        self.value = TaskResult.NoGet
        self.coroutine_worker = CoroutineWorker(work_area=task.work_area)
        self.show_str = f"<Supervisor at {hex(id(self))} wait in {task.work_area}>"

        with WorkArea(task.work_area.name):
            self.polling_func()

    def run_until_complete(self, time_out=0.1):
        """
        阻塞、工作直到轮询任务完成

        :param time_out:

            其实就是 CoroutineWorker中work_once的参数

            等待 ``WorkArea``  队列获取内容的等待超时时长

            也是最短轮询的间隔，他一般用在多线程中，当对应 ``WorkArea`` 的 ``queue`` 为空时，``time_out`` 才会触发

        :return:

            ``Task`` 类中的value，也就是对应协程的返回值
        """
        while self.wait_flag:
            with AutoCallback(None, (Empty, StopIteration)):
                # 当work_once返回false，说明是结束信号,但Supervisor暂时不考虑作处理，不然可能卡死
                _ = self.coroutine_worker.work_once(time_out)
                # 现在临时添加逻辑，当获取停止信号时，原路返回，这样可以保证不会吞结束信号
                # 但依旧可能存在协程异常退出而异步没收到的情况
                if _ is False:
                    self.coroutine_worker.submit_work(None, None, None)
        return self.value

    @coroutine
    def polling_func(self):
        """
        轮询任务，用于判断 ``Task`` 的状态

        他是一个 ``coroutine`` 修饰的协程函数

        ``Supervisor`` 会自动继承 ``Task`` 中的 ``WorkArea`` 并在此提交

        每次执行控制权切换前判断 ``Task`` 的状态是否是已完成，完成会告知 ``Supervisor``

        :return: None
        """
        while self.task.task_state is not TaskState.TaskDone:
            yield pass_func
        self.wait_flag, self.value = False, self.task.value


def wait(task, *, time_out=0.1):
    """wait阻塞等待一个Task任务完成，并在期间参与工作

    ``wait`` 是 ``Supervisor`` 类的上层封装

    简单的讲，他的作用就是轮询等待一个 ``Task``

    当这一个 ``Task`` 的状态转变为结束后 :abbr:`返回此 Task 的value (也就是对应协程函数的返回值)`

    期间他会将自身代入成为一个 ``Worker`` 进行 ``loop_work``

    某种程度上看，``wait`` 相当于特别一点的 ``loop_work`` ，主要在于他的 ``WorkArea`` 继承机制

    由于继承机制，往往你需要明确你的wait工作在哪个区域下？为哪个区域而工作？

    ``wait`` 一个 ``Task`` 时，他会继承 ``Task`` 中的 ``WorkArea`` 并生成对应的 ``CoroutineWorker`` 进行 ``loop_work``

    ``wait``  不对 :abbr:`约定的结束信号 (是自定义的一种情况，使用者基本无需关心)` 做处理
    碰到结束信号时他会重新提交回原 ``WorkArea``

    ``wait``  轮询的时间是 **不精确的** ，受到当前任务量和阻塞时间的影响

        因为 ``wait`` 的轮询任务在转移控制权的过程中，队列里依旧存在其余任务

        你无法保证下一个任务是不是阻塞的

        如果存在任务是阻塞的，那么他就有可能对 ``wait`` 照成影响

    .. tip::

        你可以通过创建 **充足的线程** 以应对这个问题，同时 **尽可能的切分函数控制权** 提高控制权转换的频率

    ``wait``  的原理是： ``wait`` 向此 ``Task`` 类中的 ``WorkArea`` 提交 一个 *轮询* 任务

    *轮询* 任务的作用就是每次执行控制权切换前判断 ``Task`` 的状态是否是已完成

    当 ``wait`` 在接收到 ``Task`` 完成信号后，会在执行完当前手头内容后退出阻塞并返回返回值

    :param Task task:

        需要等待的 ``Task`` 类, 如果传入的对象并非 ``Task`` 类，原样返回

    :param time_out:

        最短轮询的间隔，他一般用在多线程中，当对应 ``WorkArea`` 的 ``queue`` 为空时，``time_out`` 才会触发

        .. warning::

            尽可能不要设置 ``time_out`` 为 ``None``

            这或许会导致 ``wait`` 被阻塞没法正常退出

    :return: 目标 ``Task`` 中的 ``value``
    """
    return Supervisor(task).run_until_complete(time_out) if isinstance(task, Task) else task
