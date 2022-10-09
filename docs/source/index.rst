.. consign documentation master file, created by
   sphinx-quickstart on Thu Oct  6 13:25:01 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

consign
===================================

.. toctree::
   :hidden:
   :maxdepth: 2

   modules
   api

   .. consign.decorator
   .. consign.workarea
   .. consign.worker
   .. consign.utils

   GitHub page <https://github.com/SpectrePrediction/consign>

.. image:: https://img.shields.io/badge/consign-1.0.2-blue
   :alt: 版本

.. image:: https://readthedocs.org/projects/consign/badge/?version=latest
    :target: https://consign.readthedocs.io/zh_CN/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/v/release/SpectrePrediction/consign
   :alt: GitHub release (latest by date)

Generator-based Coroutines, Easy to use, Using the yield syntax

consign 是基于 ``generator`` 的协程框架，易于使用，使用 ``yield`` 语法，同时允许普通函数和生成器函数 

consign 可以使函数得以以协程的方式运行，以更低的代码侵入性，获得更高的效率

.. warning::
   
   由于依托 ``generator`` 的缘故，consign中的异步在 **Win环境** 下 **无法使用多进程** ，目前未测试其他系统。
   
   因为目前 **没有库支持反序列化**  ``generator`` 。
   
   而需要序列化好像是因为Win中没有 ``os.fork`` ，只能去模拟，所以 **不知道Unix系统能不能使用多进程** 。

   你是 **可以在多进程的程序中使用consign** ，但存在一定限制（并不大），建议使用 **组合** 替代 **继承** 可以避免大部分问题。

----

文档介绍
--------------

`文档 <https://consign.readthedocs.io/zh_CN/latest/>`_ 使用 *Sphinx* 框架， *furo* 主题

.. tab-set::

    .. tab-item:: 回到此页

        需要回到 :abbr:`此页面 (index.html)` 可以通过点击左上角的 ``consign文档`` 字样

    .. tab-item:: 搜索框

        左侧是搜索框可以直接查询函数
        
        注意的是函数结果可能有多个，同名的函数却在不同长短的路径下。
        
        这不影响，因为他们都是相同的内容，只是路径不同。

        建议选择路径最全的 ``包名+模块名+文件名+类`` ，他们通常可以通过点击 ``源代码`` 跳转到GitHub中的源代码

    .. tab-item:: consign

        左侧侧边栏的consign 通过点击可以查看全部函数列表。

        .. attention::

           :abbr:`直接查看的函数 (即没有完整路径的函数)` 点击 ``源代码`` 几乎无法跳转到源代码 

           这是由于自动生成文档导致的

           解决办法是通过找到consign中靠后的 ``consign.xxx package`` 中具体的 ``xxx Module`` 中的函数
           
           点击正确的函数后提示的 ``源代码`` 才能正确跳转GitHub源代码，多多担待

           .. tip::

              或者通过 ``API`` 中找到对应函数并跳转也是可以的

    .. tab-item:: API

        左侧侧边栏的api 是consign 全模块的概览图。

        你可以快速访问模块下具体有那些文件，以及获得每个文件中的函数列表以及他们的一句话描述。

        如果需要查看函数详细，可以点击函数名跳转到具体函数页面

    .. tab-item:: 其他

        .. seealso::
           
           存在部分不导出的函数，即无法通过直接从consing库中得到的函数，他们通常是其他函数的基石

           只能在靠后的 ``consign.xxx package`` 中具体的 ``xxx Module`` 中，或者 ``API`` 中 查看

           :sub:`我写了注释但不知道为什么autodoc不对他们起作用，或许是配置不正确？` 

        如果你对他们的实现感兴趣，最好直接看GitHub源代码，我都留了注释

----

快速开始
--------------

``python>=3.7`` ：consign 几乎没有需要安装的依赖
反之会需要安装 ``contextvars`` ，仅此而已

你可以通过 ``pip`` 快速安装:

.. code-block:: python

   pip install pyconsign


或者通过 ``git`` 开箱即用

.. code-block:: python

   python setup.py install

:sub:`为什么不是pip install consign呢？ 因为consign已经被占用了`

.. seealso::

   现经测试,在 :abbr:`win10 python 3.6-3.9 (理论上python>=3.4版本兼容)` 中运行良好，将会完成更多测试

----

例子
--------------

:abbr:`最简单的 (处于cmd模式下)`

.. tab-set::

    .. tab-item:: CoroutineWorker

        .. code-block:: python
  
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

    .. tab-item:: AsyncWorker

        .. code-block:: python
  
           >>> from consign import coroutine, asleep, AsyncWorker
           >>> import threading, time
           >>> @coroutine
           ... def my_test(name: str):
           ...     print(f"{name} start in {threading.currentThread()}")
           ...     result = yield time.sleep(3)
           ...     print(f"{name} end in {threading.currentThread()} result is {result}")
           ...     return name
           ...
           >>> aw = AsyncWorker()
           >>> aw.init_thread(5)
           >>> test_task1, test_task2 = my_test("task1"), my_test("task2")
           task1 start in <DummyProcess(consign_98cfdee9-aea0-47d7-b501-0b5bfd277a39, started daemon 22920)>
           task2 start in <DummyProcess(consign_184134fe-2fbe-4161-8458-d186aba693e8, started daemon 31020)>
           task1 end in <DummyProcess(consign_98cfdee9-aea0-47d7-b501-0b5bfd277a39, started daemon 22920)> result is None
           task2 end in <DummyProcess(consign_184134fe-2fbe-4161-8458-d186aba693e8, started daemon 31020)> result is None
           >>> test_task1
           {
              'task_state': <TaskState.TaskDone: 'TaskDone'>,
              'value': 'task1', 
              'work_area': <'DEFAULT_WORK_AREA' Work at 0x1b7034046d8 and in <_MainThread(MainThread, started 17700)>>, 
              'order': {
                 'consignor_func': <function my_test at 0x000001B701572EA0>, 
                 'create_area': <'DEFAULT_WORK_AREA' Work at 0x1b7034046d8 and in <_MainThread(MainThread, started 17700)>>, 
                 'create_callback': None, 
                 'complete_callback': None
              }
           }

细节部分解释

.. tab-set::

    .. tab-item:: coroutine

        @coroutine是修饰器，也是consign的关键， **他修饰的函数会以委托协程的方式运行** 。
        
        如果函数是一个 **生成器函数** ，那么当函数运行到yield时会 **被切换控制权** 。
        
        如果函数是 **非生成器函数** ，那么@coroutine会将其 **包装成生成器函数** 并继续下去，但同时也失去了函数内控制权切换的能力

        @coroutine会生成一些信息 ``ConsignOrder`` ，以及每次运行时也会生成 ``Task`` 

        所有被修饰的函数都会变成 **非阻塞的** ，他们的返回值 **被Task类替代** ，Task中存放着包括返回值在内的全部信息

    .. tab-item:: yield

        yield是 **控制权转移的关键** ，consign在单线程下依旧以并发的形式运行，关键就在于yield。

        consign 允许 yield **任意内容** ， 但比较特殊的是function。
        
        如果是 **非function内容** ，返回的值是本身，同时切换控制权，这没什么好说的。

        如果yield的是一个function, **则需要function是一个无参函数**

        .. tip::

           你可以通过很多方法实现将一个有参函数再次无参形式调用：

           consign中的 ``repeated_call`` ，functools中的 ``partial`` 以及class中的 ``__call__`` 方法

        满足条件的function会在yield后由consign执行
        
        大部分情况下，你可以直接在yield前调用function， **这其实意味着你yield的是调用函数后的返回值** 。

        .. tip::

           特殊的情况一般是留给需要yield一个同样被@coroutine修饰的协程函数时使用的
           
           他可以和 :abbr:`链式反应 (chain_reaction)` 和 :abbr:`等待 (wait)` 一同使用达到事半功倍的效果

           .. warning::
              
              注意：yield function 这个条件可能在未来删除，他其实是我 :abbr:`为了兼容旧版框架留下的 (旧版的consign并不成熟，所以没有开源，但我存在项目还在使用他)`
           
        无需在此留下太多的注意力， :sub:`好吧我承认这是设计上的失误，曾经的`


    .. tab-item:: worker

        ``AsyncWorker`` 继承自 ``CoroutineWorker`` ，他们有些许不同
        
        如果你使用 ``AsyncWorker`` ，那么 ``loop_work(forever=False)``  **在切换很快时是不可信的**  
        
        :abbr:`这是由于队列qsize不确定性 (官方的描述:由于多线程或者多进程的上下文，这个数字是不可靠的。请注意，这可能会在Unix平台上引起 NotImplementedError)` 以及框架的获取提交导致的
        
        .. tip::

           通常在多线程下使用 ``loop_work(forever=True)`` 或者重复 ``while True`` 使用 ``loop_work(forever=False)`` 

        loop_work会把当前线程 **阻塞** 并作为一个 **临时的worker** 去工作
        
        所以如果 ``AsyncWorker`` 不使用 ``init_thread`` 直接使用 ``loop_work`` 其实和 ``CoroutineWorker`` 效果是 **相同的** 
        
        都是使用 **主进程** 去工作，是 **单线程** 的，所以任何阻塞的函数都会导致阻塞。

        .. tip::

           你可以从代码中注意到
           
           ``AsyncWorker`` 提前于函数执行前使用了 ``init_thread(5)`` ，这意味着 ``AsyncWorker`` 创建了5个线程
           
           他们会一同去处理所有的协程，所以我无需使用 ``loop_work`` ，协程函数就能被瓜分执行

           如果你不使用 ``init_thread`` ， 那么 ``AsyncWorker`` 会很失望的
           
           （当然！你可以使用create_thread创建单个线程，他其实是init_thread的一部分）

        ``AsyncWorker`` 创建的线程默认是 **守护线程** ，如果你的程序没有阻塞一路到exit的话，可能导致协程任务异常被终止
        
        所以在 **非cmd** 下，最好使用 ``while True`` 或者 ``loop_work(forever=True)`` 去阻塞，或者设置参数选择生成非守护线程。

        生成线程的名字如果没有传参，那么默认是uuid的
        
        所以会出现 *consign_184134fe-2fbe-4161-8458-d186aba693e8* 这种名字，具体需要去看文档。

    .. tab-item:: sleep

        sleep是有点不同的， **asleep是consign实现的** ， 他其实 **也是被修饰的协程函数** 。 
        
        他其实是 **在不停的切换控制权** 通过consign来实现并发的，所以他是 **非阻塞** 的。
        
        这也是consign能在单线程下并发的原因：控制权切换
        
        同时也是大部分协程的缩影。而 ``time.sleep`` 是 **阻塞** 的。

        但为什么后面使用了 ``time.sleep`` 呢？因为我们通过这个sleep来模拟一个阻塞的，非协程的io函数。
        
        你可以看到， ``AsyncWorker`` 通过多线程完成了这一切, 使得 ``time.sleep`` 的效果和 ``asleep`` 相同。

        .. warning::

           如果使用 ``CoroutineWorker`` 或者 ``AsyncWorker`` 创建的线程都被阻塞了，那么依旧会产生阻塞的效果。

           当然，你可以创建 **充足的线程** 以应对这个问题，同时 **尽可能的切分函数控制权** 也可以充分利用consign

    .. tab-item:: task

        Task是什么？他是 **每次协程函数运行时** 产生的 **类** ，同时也是协程函数的 **替代返回值** 。

        Task里存放则很多信息，包括协程此次任务的完成情况，函数的返回值。

        .. warning::
        
           他很重要，是协程的运行的基础，部分信息被用在处理过程中，所以如果你要 **修改** ， **最好知道他是要做什么的** 

        Task被打印成一个字典，但Task其实并非是字典而是类，所以如果需要获取其值，通过 **类成员** 而非 **下标** 或者 **key** 去访问

        当然Task也提供以字典方式访问的功能，但并不划算

    .. tab-item:: 一个看不见的恶魔

        哈哈！开个玩笑，但看不见是真的，他很重要，他就是 ``WorkArea`` 。

        WorkArea详情可以去看文档，简要的来说，你看起来没有设置过 ``WorkArea`` ，其实使用的就是默认的 ``WorkArea`` ，他的变量名是 ``DEFAULT_WORK_AREA`` 。

        .. note::

           一旦你导入了consign， ``DEFAULT_WORK_AREA`` 就会被创建并指定一个 ``WorkArea`` 
           
           所有没有被 :abbr:`上下文管理器 (with)` 包裹的协程其实都是运行在名为DEFAULT_WORK_AREA的WorkArea上。

           没有指定名字的Worker其实是为默认 也就是DEFAULT_WORK_AREA的WorkArea 工作的

        你可以通过直接访问 ``DEFAULT_WORK_AREA`` 这个变量，但一般不建议
        
        ``DEFAULT_WORK_AREA`` 同样被创建在 ``builtins`` 中，所以他无需从consign包名下使用，即使例如PyCharm提示变量不存在

        所有的 ``Worker`` 同理，他们需要传入 ``WorkArea`` 名或者类，这表明这个Worker是为哪个WorkArea在服务。
        
        不同的 ``WorkArea`` 会相互隔离，但注意的是， **同名的WorkArea视作同一个WorkArea** ，同名WorkArea是 **单例** 的。

        :sub:`他其实不可怕，他能方便你去管理Worker和分配协程函数，他的使用方法在文档中，感兴趣就去看看吧`


consign 更适合和一些特别的情况发生化学反应，我们来看看更多例子，并开始慢慢了解

----

更多例子
--------------

让我们来看看比较常见的写法

.. code-block:: python

   from consign import coroutine, wait, AsyncWorker
   import time

   DEBUG = False

   @coroutine(DEBUG)
   def my_io_read(path: str):
      print(f"Let me start reading {path}", threading.currentThread())
      yield time.sleep(3)
      print(f"reading {path} over", threading.currentThread())
      return f"<{path} read data>"

   @coroutine(DEBUG)
   def preprocess(path: str):
      print(f"preprocess {path} somethings", threading.currentThread())
      yield time.sleep(1.5)
      print(f"preprocess {path} is over", threading.currentThread())
      return f"<preprocess {path}>"

   @coroutine(DEBUG)
   def my_test(path: str):
      print(f"my_test start and path is {path}", threading.currentThread())
      data_task = yield my_io_read(path)
      some_preprocess_task = yield preprocess(path)
      data, some_preprocess = wait(data_task), wait(some_preprocess_task)
      print(f"my_test over {some_preprocess} and data is {data}", threading.currentThread())


   aw = AsyncWorker()
   using_thread_num = 5
   aw.init_thread(using_thread_num, name_iter=(f"DEFAULT_WORK_AREA_{i}" for i in range(using_thread_num)))

   my_test("test/task1.jpg")
   my_test("test/task2.jpg")

   aw.loop_work(forever=True)

输出的结果是:

.. code-block:: none

   my_test start and path is test/task1.jpg <_MainThread(MainThread, started 29856)>
   my_test start and path is test/task2.jpg <DummyProcess(consign_DEFAULT_WORK_AREA_1, started daemon 35364)>
   Let me start reading test/task1.jpg <_MainThread(MainThread, started 29856)>
   Let me start reading test/task2.jpg <DummyProcess(consign_DEFAULT_WORK_AREA_1, started daemon 35364)>
   preprocess test/task1.jpg somethings <DummyProcess(consign_DEFAULT_WORK_AREA_3, started daemon 36668)>
   preprocess test/task2.jpg somethings <DummyProcess(consign_DEFAULT_WORK_AREA_4, started daemon 37204)>
   preprocess test/task1.jpg is over <DummyProcess(consign_DEFAULT_WORK_AREA_3, started daemon 36668)>
   preprocess test/task2.jpg is over <DummyProcess(consign_DEFAULT_WORK_AREA_4, started daemon 37204)>
   reading test/task1.jpg over <DummyProcess(consign_DEFAULT_WORK_AREA_0, started daemon 37332)>
   reading test/task2.jpg over <_MainThread(MainThread, started 29856)>
   my_test over <preprocess test/task2.jpg> and data is <test/task2.jpg read data> <DummyProcess(consign_DEFAULT_WORK_AREA_0, started daemon 37332)>
   my_test over <preprocess test/task1.jpg> and data is <test/task1.jpg read data> <DummyProcess(consign_DEFAULT_WORK_AREA_4, started daemon 37204)>

值得注意的点：

.. tab-set::

    .. tab-item:: DEBUG

        DEBUG是全局标志，他会在程序被创建时决定了 ``@coroutine`` 是否以协程的方式运行

        如果DEBUG=True，那么所有被传递参数的 ``@coroutine`` 修饰器，都会退化成普通函数的线性运行方式而无需改动代码

        .. seealso::

           由于无需改动代码，事实上函数类型没变，只是 ``@coroutine`` 会返回一个替代的函数

           如果原修饰函数是普通函数，那么替代函数直接返回结果

           如果原修饰函数是生成器函数，这个替代函数内部会阻塞并不断的next，直到生成器函数运行完毕后返回结果
         
        DEBUG仅在程序初次加载时起作用，后续修改变量无效

    .. tab-item:: wait

        wait的作用是等待一个Task完成，期间他会将自身代入成为一个 ``Worker`` 进行 ``loop_work`` 

        wait很特殊，他可以理解成一个特殊的 ``loop_work`` ，为什么特殊主要在于他的 ``WorkArea`` 继承机制 
        
        他内部组合了 ``CoroutineWorker`` , 简单说几个特性：

        1. wait一个Task时，他会继承Task中的 ``WorkArea`` 并生成对应的 ``CoroutineWorker`` 进行 ``loop_work`` 

        2. wait不对 :abbr:`约定的结束信号 (是自定义的一种情况，使用者基本无需关心)` 做处理，碰到结束信号时他会重新提交回原 ``WorkArea`` 

        3. wait轮询的时间是不精确的，受到当前任务量和阻塞时间的影响

        通常wait很好理解，但是当使用 ``WorkArea`` 时，由于继承机制，往往你需要明确你的wait工作在哪个区域下？为哪个区域而工作？

        当然，这也是wait的特性之一，用的好的话是可以产生奇妙的化学反应，比如实现协程分配者

更多例子还在完善中...

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
