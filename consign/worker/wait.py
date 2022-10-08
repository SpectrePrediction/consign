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

    def __init__(self, task):
        self.task = task
        self.wait_flag = True
        self.value = TaskResult.NoGet
        self.coroutine_worker = CoroutineWorker(work_area=task.work_area)
        self.show_str = f"<Supervisor at {hex(id(self))} wait in {task.work_area}>"

        with WorkArea(task.work_area.name):
            self.polling_func()

    def run_until_complete(self, time_out=0.1):
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
        while self.task.task_state is not TaskState.TaskDone:
            yield pass_func
        self.wait_flag, self.value = False, self.task.value


def wait(task, *, time_out=0.1):
    """
    某种程度上，他相当于特别一点的loop_work

    作用是：等待一个task，当这一个task的状态转变为结束后，返回此task的value

    原理是：向此Task类中的work area提交 一个轮询任务，他的作用就是调用时判断task是否完成
        同时wait会启动一个补偿Worker，他会阻塞并如同Worker一般处理work area中的事物，直到轮询任务告知task已经完成，
            wait才会结束阻塞，并返回Worker

    需要注意的点：
        补偿Worker不会受到Worker约定的结束符信号，他会略过并继续运行，这是个不足之处，可能导致预期之外的结束失败
            在旧版本中，协程Worker和异步协程Worker的处理过程是有区别的，现在新版他们统一使用一套逻辑（异步Worker是组合了
            协程Worker），所以导致原本应当传递给异步的Worker结束符有可能被协程Worker捕获（如果同时存在两者且同时运行在同
            个work area中），就有可能导致异步Worker并没有预期中的结束，或者协程Worker的Loop Work被意外结束，又或者无事发生
            同时如果传递多个结束符，可能导致队列中有额外的残留，导致下次运行时Worker意外结束，所以未来版本应该会清理队列
        wait轮询的时间是不精确的，timeout只能设定最短的轮询间隔，但事实上单线程协程最短没有轮询间隔，他应当是在轮询任务
            和被轮询状态任务之间交替执行的，但主要是为了适配多线程，可能存在补偿Worker等待不到任务，则通过time_out去轮询
            设置为None导致补偿Worker会一直等待get任务，从而忽略了更新状态，这是不建议的

    :param task: 需要监视的task类
    :param time_out: 最短轮询的间隔，为None只会在worker每次工作完成才轮询
    :return:
    """
    return Supervisor(task).run_until_complete(time_out) if isinstance(task, Task) else task
