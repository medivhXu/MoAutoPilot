import traceback
import functools
from loguru import logger


def logged(func):
    """创建一个日志装饰器，它会记录所装饰函数的入参和
    """
    result = None

    @functools.wraps(func)
    def inner(*args, **kwargs):

        try:
            nonlocal result
            result = func(*args, **kwargs)
            # logger.info('模块:{}\n 调用函数 {} 传入参数: {},{}\n 返回结果: {}'
            #             .format(inspect.getmodule(func), func.__name__,
            #                     args, kwargs, result))
            return result
        except Exception as Ex:
            logger.error("{}方法入参:{},{}".format(func.__name__, args, kwargs))
            e = traceback.format_exc()
            logger.error('Exception：{}'.format(e))
            raise Ex

    return inner
