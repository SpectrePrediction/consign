import time
import threading

from consign import WorkArea
from consign import coroutine, asleep, wait
from consign import CoroutineWorker, AsyncWorker


DEBUG = False


@coroutine(DEBUG)
def asleep_run(name: str):
    print("Hello world! ", name, threading.currentThread())

    yield asleep(1)
    print("Middle! ", name, threading.currentThread())

    yield asleep(1)
    print("Over! ", name, threading.currentThread())
    return name


def test_coroutine_worker():
    with WorkArea.as_default():
        asleep_run("asleep_run task1")
        assert wait(asleep_run("asleep_run task2")) == "asleep_run task2"
        CoroutineWorker().loop_work(forever=False)


@coroutine(DEBUG)
def my_io_read(path: str):
    print("Let me start reading ", path, threading.currentThread())

    yield time.sleep(3)

    print("reading {path} over".format(path=path), threading.currentThread())
    return "<{path} read data>".format(path=path)


@coroutine(DEBUG)
def preprocess(path: str):
    print("preprocess {path} somethings".format(path=path), threading.currentThread())

    yield time.sleep(1.5)

    print("preprocess {path} is over".format(path=path), threading.currentThread())
    return "<preprocess {path}>".format(path=path)


@coroutine(DEBUG)
def time_sleep_run(path: str):
    print("my_test start and path is ", path, threading.currentThread())

    data_task = yield my_io_read(path)
    some_preprocess_task = yield preprocess(path)

    data, some_preprocess = wait(data_task), wait(some_preprocess_task)

    print("my_test over {some_preprocess} and data is {data}".format(
        some_preprocess=some_preprocess, data=data), threading.currentThread())
    return path


def test_async_worker():
    with WorkArea.as_default():
        AsyncWorker().init_thread(4)
        time_sleep_run("time_sleep_run task1")
        assert wait(time_sleep_run("time_sleep_run task2")) == "time_sleep_run task2"
