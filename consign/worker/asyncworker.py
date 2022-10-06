# import threading
# dummy相当于threading的封装，他能很好的修改成多进程支持，方便在io密集和cpu密集中做出取舍
# 但值得一提的是，目前不支持多进程，因为修饰器的关系（work_area被修饰)，将在下版本更新
from multiprocessing.dummy import Process, current_process
from uuid import uuid4
from itertools import repeat

from .coroutineworker import CoroutineWorker
# from ..decorator import coroutine


class AsyncWorker(CoroutineWorker):

    def __init__(self, work_area_name: str = "DEFAULT_WORK_AREA", *, work_area=None):
        """
        继承CoroutineWorker，实现创建线程以达成异步的作用
        异步AsyncWorker可以将耗时的事情交给线程去处理，其他的任务被执行
            当然，如果你使用了链式反应，那么他依旧还是顺序的，所以如果有性能上的要求，建议不使用链式反应，转而使用wait
        :param work_area_name: 同CoroutineWorker，就不重复了
        :param work_area: 同CoroutineWorker，就不重复了
        """

        super(AsyncWorker, self).__init__(work_area_name, work_area=work_area)
        self.show_str = f"<AsyncWorker at {hex(id(self))} work in {self.work_area}>"
        # __thread_list不对外暴露，对外建议使用thread_list
        self.__thread_list = []

    @property
    def thread_list(self):
        # 在获取thread_list时，同时检测并删除__thread_list中已经关闭的线程
        self.clear_dead_thread()
        # 返回处理后的情况，注意这个处理会同步修改到__thread_list，所以返回的并不是副本，请不要滥用
        return self.__thread_list

    def clear_dead_thread(self):
        [self.__thread_list.remove(thread) for thread in self.__thread_list if not thread.is_alive()]

    def create_thread(self, name=None, daemon=True):
        """
        创建一个协程线程
        本来想作为一个静态方法的，全部共享一个静态__thread_list，但考虑到work area，这么做不合理，遂罢
        :param name: 创建的线程名
        :param daemon: 是否守护线程
        :return: consign_thread 创建的线程对象
        """
        # consign_thread = threading.Thread(target=self.loop_work, name=f"consign_{name or uuid4()}")
        consign_thread = Process(target=self.loop_work, name=f"consign_{name or uuid4()}")
        self.__thread_list.append(consign_thread)
        consign_thread.daemon = daemon
        consign_thread.start()
        return consign_thread

    def init_thread(self, create_num, name_iter=None, daemon=True):
        """
        一次初始化多个线程
        :param create_num: 创建数量
        :param name_iter: 名字生成器或者列表，如果没有默认使用uuid
            请注意：没有对其长度做校验，但应该跟create_num做对应
        :param daemon: 创建的是否是守护线程，无论你数量有多少
        :return:
        """
        tuple(map(self.create_thread, name_iter or repeat(None, create_num), repeat(daemon, create_num)))

    def submit_thread_stop_flag(self):
        # 提交约定的结束信号，但注意，约定的结束信号不一定能立马结束，因为队列中可能还有其他内容
        # 同时可能被其他Worker接收，比如协程Worker，所以复杂情况下结果并不确定
        self.submit_work(None, None, None)

