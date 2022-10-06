# 负责工作区域分划，每个工作区域存在一个队列，所以的委托都会被提交在次
# 程序被导入时，会创建默认的工作区域，所有的worker工作者都会去获取工作区域
import builtins
from contextvars import ContextVar

from .workarea import WorkArea, _instance_dict
DEFAULT_WORK_AREA = \
    builtins.DEFAULT_WORK_AREA = ContextVar("DEFAULT_WORK_AREA", default=WorkArea(name="DEFAULT_WORK_AREA"))

WORK_AREA_DICT = builtins.WORK_AREA_DICT = _instance_dict
