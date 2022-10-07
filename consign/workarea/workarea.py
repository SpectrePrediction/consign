import builtins

from queue import Queue, LifoQueue
# from multiprocessing import Queue
from functools import wraps
from contextvars import ContextVar
from threading import currentThread  # , Lock
from multiprocessing.dummy import Lock
# from multiprocessing.dummy import current_process


# _instance_dict 在init中被取别名为 WORK_AREA_DICT 并置入 builtins
_instance_dict = {}


# def same_name_singleton(cls):
#     _instance_lock = Lock()
#     # _instance_dict = {}
#
#     @wraps(cls)
#     def inner(name: str="DEFAULT_WORK_AREA"):
#         # name = kwargs.get("name", None) or args[0]
#
#         if _instance_dict.get(name, None) is None:
#             with _instance_lock:
#                 _instance_dict[name] = cls(name)  # (*args, **kwargs)
#         return _instance_dict[name]
#
#     inner.as_default = cls.as_default
#     return inner


class SameNameSingleton(type):
    _instance_lock = Lock()

    def __init__(cls, *args, **kwargs):
        """
        为了适配未来可能的多进程，使用元类可以过序列化而无需额外使用dill
        :param args:
        :param kwargs:
        """
        super(SameNameSingleton, cls).__init__(*args, **kwargs)

    def __call__(cls, name: str="DEFAULT_WORK_AREA", *args, **kwargs):
        if _instance_dict.get(name, None) is None:
            with cls._instance_lock:
                _instance_dict[name] = super(SameNameSingleton, cls).__call__(name, *args, **kwargs)
        return _instance_dict[name]


# @same_name_singleton
class WorkArea(metaclass=SameNameSingleton):

    def __init__(self, name: str="DEFAULT_WORK_AREA"):
        """
        WorkArea 分离所有Work的工作区域：
            这可以有助于你分配资源以及更好的使用Worker

        WorkArea 被设计成线程安全的：
            借助ContextVar在每个线程中都拥有独立的值，其本质是threading.local

        WorkArea 默认在导入此库时，创建默认的 DEFAULT_WORK_AREA 变量作为默认工作地址，并置于builtins中：
            这意味着你可以通过 直接访问 DEFAULT_WORK_AREA.get() 获取当前的工作区域，当然并不推荐，一旦你这样使用，你应当
            ——明白你想要做些什么，以及会造成那些影响
            DEFAULT_WORK_AREA 是全局的统一的，依托ContextVar可以实现在不同线程中不同的值，不同线程间修改不会出现相互影
            ——响，WorkArea作为上下文管理器其实现的本质就是对DEFAULT_WORK_AREA的修改和恢复，所以理论上在同一线程中使用
            ——WorkArea，WorkArea会修改DEFAULT_WORK_AREA的值来影响此线程Work的运行，这也许会导致WorkArea相互干扰（如果
            ——WorkArea在线程中是并行或者并发的）。但这只存在理论上，ContextVar应当对官方的协程也支持良好，所以不会干扰

        WorkArea 本质是一个上下文管理器，但同时支持修饰器写法：
            修饰器代码来源于ContextDecorator
            修饰器写法相当于语法糖：
                def f():                    @cm()
                    with cm():       —>    def f():
                        # Do stuff              # Do stuff

        WorkArea 的name参数非常重要:
            你可以注意到WorkArea被same_name_singleton修饰，same_name_singleton是单例的修饰器
            (新版本，为了适配多进程，修饰器无法被序列化，所以改用元类进行单例，效果不变）
            WorkArea通过name区分区域，同名（name相同，区分大小写）的情况下区域内只有一个WorkArea实例，但值得注意的是：
                即使是同一个单例WorkArea，也并不意味着其中old_work_area_queue的变量存放的值是相同的
                old_work_area_queue的本质是被ContextVar包裹的变量，为了防止多线程中共用一个WorkArea导致的LifoQueue顺序冲
                ——突，old_work_area_queue会在每个单独的线程中创建一个LifoQueue，由线程共享，以此保证线程安全

        :param name: WorkArea区域的名字，同名WorkArea是同一个实例， 默认是DEFAULT_WORK_AREA
            tips: 建议输入是str，但理论上能hash的值都能传入，但不保证不出错
        """
        self.name = name
        self.show_str = f"<'{name}' Work at {hex(id(self))}"
        # win 环境下 multiprocessing 的 Queue 无法序列化 generator，所以暂时没有办法做适配，期待下版本更新
        self.queue = Queue()
        # 使用LifoQueue先进后出队列是为了兼容 同名区域单例模式下 被嵌套的情况
        # 使用ContextVar上下文变量是为了兼容 同名区域单例模式下 多线程中队列顺序冲突的情况
        self.old_work_area_queue = ContextVar(f"{name}_LifoQueue", default=None)

    def __enter__(self):
        """

        :return:
        :raise: Full(LifoQueue put_nowait引发）
        """
        # self.old_work_area = builtins.DEFAULT_WORK_AREA.set(self)
        if self.old_work_area_queue.get() is None:
            # 在此处更新 ContextVar上下文变量 以此保证在一个线程一个队列
            self.old_work_area_queue.set(LifoQueue())
        self.old_work_area_queue.get().put_nowait(builtins.DEFAULT_WORK_AREA.set(self))

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """

        :param exc_type:
        :param exc_value:
        :param exc_tb:
        :return:
        :raise: Empty(LifoQueue get_nowait引发）， RuntimeError、ValueError（ContextVar reset引发）
        """
        # builtins.DEFAULT_WORK_AREA.reset(self.old_work_area)
        builtins.DEFAULT_WORK_AREA.reset(self.old_work_area_queue.get().get_nowait())

    @staticmethod
    def as_default():
        """
        使用 as_default 将会去 builtins 中寻找 DEFAULT_WORK_AREA 变量并返回其中保存的WorkArea
        DEFAULT_WORK_AREA 变量一般会在导入 work area 库时被创建
        如果没能找到，as_default 会将自身包装、置入builtins并返回自身
        :return:
        :raise:
        """
        default = getattr(builtins, "DEFAULT_WORK_AREA", None)
        if default is None:
            default = ContextVar("DEFAULT_WORK_AREA", default=WorkArea("DEFAULT_WORK_AREA"))
            setattr(builtins, "DEFAULT_WORK_AREA", default)
        return default.get()
        # return getattr(builtins, "DEFAULT_WORK_AREA", None) or ContextVar(self.show_str, default=self._recreate_cm())

    def _recreate_cm(self):
        """Return a recreated instance of self.

        Allows an otherwise one-shot context manager like
        _GeneratorContextManager to support use as
        a decorator via implicit recreation.

        This is a private interface just for _GeneratorContextManager.
        See issue #11647 for details.
        """
        return self

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            with self._recreate_cm():
                return func(*args, **kwargs)
        return inner

    def __str__(self):
        return f"{self.show_str} and in {currentThread()}>"

    __repr__ = __str__

