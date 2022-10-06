import builtins
from enum import Enum


class TaskResult(Enum):
    NoGet = "NoGet"


class TaskState(Enum):
    NoStart = "NoStart"
    RunCreateCallBack = "RunCreateCallBack"
    TaskRunning = "TaskRunning"
    RunCompleteCallBack = "RunCompleteCallBack"
    TaskDone = "TaskDone"


class Task(object):
    def __init__(self, order):
        """
        单次任务清单

        通过create_receipts函数创建回执
        回执 被用来得到协程的函数返回值
        清单本身 被用来告知外界协程的情况

        """
        self.order = order
        self.create_callback = order.create_callback
        self.complete_callback = order.complete_callback
        self.consignor_func = order.consignor_func

        self.work_area = builtins.DEFAULT_WORK_AREA.get()
        self.task_state = TaskState.NoStart
        self.value = TaskResult.NoGet

    def create_receipts(self):
        """
        不建议自行调用，它会在被修饰函数启动时创建
        :return:
        """
        self.create()

        self.task_state = TaskState.TaskRunning
        self.value = yield self.consignor_func
        self.complete()
        self.task_state = TaskState.TaskDone

    def create(self):
        if self.create_callback is not None:
            self.task_state = TaskState.RunCreateCallBack
            self.create_callback(self)

    def submit(self, something):
        self.work_area.queue.put(something)

    def complete(self):
        if self.complete_callback is not None:
            self.task_state = TaskState.RunCompleteCallBack
            self.complete_callback(self)

    def all_info(self):
        return {
            "task_state": self.task_state,
            "value": self.value,
            "work_area": self.work_area,
            "order": self.order
        }

    def __str__(self):
        return str(self.all_info())

    __repr__ = __str__
