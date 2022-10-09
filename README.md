<h1 align="center">Consign</h1>

<p align="center">
  Generator-based Coroutines, Easy to use, Using the yield syntax
</p>
<p align="center">
 consign 是基于 generator 的协程框架，易于使用，使用 yield 语法
</p>

---

![版本](https://img.shields.io/badge/consign-1.0.2-blue) | [![Documentation Status](https://readthedocs.org/projects/consign/badge/?version=latest)](https://consign.readthedocs.io/zh_CN/latest/?badge=latest) | ![GitHub release (latest by date)](https://img.shields.io/github/v/release/SpectrePrediction/consign)

<p align="center">
  consign 可以使函数得以以协程的方式运行，以更低的代码侵入性，获得更高的效率
</p>

### 快速开始
consign 几乎没有需要安装的依赖，在GitHub中开箱即用即可

更多信息请查看 [consign's documentation](https://consign.readthedocs.io/zh_CN/latest/)

### 简单例子

初探特性

``` python

>>> from consign import coroutine, asleep, CoroutineWorker
>>> import threading
>>> @coroutine
... def my_test(name: str):
...     print(f"{name} start in {threading.currentThread()}")
...     result = yield asleep(3)
...     print(f"{name} end in {threading.currentThread()} result is {result}")
...     return name
...
>>> test_task1, test_task2 = my_test("task1"), my_test("task2")
>>> test_task1
{
    'task_state': <TaskState.NoStart: 'NoStart'>, 
    'value': <TaskResult.NoGet: 'NoGet'>, 
    'work_area': <'DEFAULT_WORK_AREA' Work at 0x25940db46a0 and in <_MainThread(MainThread, started 31352)>>, 
    'order': {
        'consignor_func': <function my_test at 0x000002593EEF2EA0>, 
        'create_area': <'DEFAULT_WORK_AREA' Work at 0x25940db46a0 and in <_MainThread(MainThread, started 31352)>>,
        'create_callback': None,
        'complete_callback': None
    }
}
>>> CoroutineWorker().loop_work(forever=False)
task1 start in <_MainThread(MainThread, started 24332)>
task2 start in <_MainThread(MainThread, started 24332)>
task1 end in <_MainThread(MainThread, started 24332)> result is None
task2 end in <_MainThread(MainThread, started 24332)> result is None
>>> test_task1
{
    'task_state': <TaskState.TaskDone: 'TaskDone'>,
    'value': 'task1', 
    'work_area': <'DEFAULT_WORK_AREA' Work at 0x23fbe9f46d8 and in <_MainThread(MainThread, started 24332)>>, 
    'order': {
        'consignor_func': <function my_test at 0x0000023FBCB42EA0>, 
        'create_area': <'DEFAULT_WORK_AREA' Work at 0x23fbe9f46d8 and in <_MainThread(MainThread, started 24332)>>, 
        'create_callback': None, 
        'complete_callback': None
    }
}
```

---

更多还在路上...

## License

This project is licensed under the MIT License. 享受开源