# _*_ coding:UTF-8 _*_

import os
import sys
import json
import time
import inspect
import functools
import traceback
from copy import copy
from .logger import get_logger
from .snippet import reg_cleanup
LOGGING = get_logger(__name__)


class AirtestLogger(object):
    """logger """
    def __init__(self, logfile):
        super(AirtestLogger, self).__init__()
        self.running_stack = []
        self.extra_log = {}
        self.logfile = None
        self.logfd = None
        self.set_logfile(logfile)
        reg_cleanup(self.handle_stacked_log)

    def set_logfile(self, logfile):
        if logfile:
            self.logfile = os.path.realpath(logfile)
            self.logfd = open(self.logfile, "w")

    @staticmethod
    def _dumper(obj):
        try:
            d = copy(obj.__dict__)
            try:
                d["__class__"] = obj.__class__.__name__
            except AttributeError:
                pass
            return d
        except AttributeError:
            return None

    def log(self, tag, data, depth=None):
        ''' Not thread safe '''
        # LOGGING.debug("%s: %s" % (tag, data))
        if depth is None:
            depth = len(self.running_stack)

        if self.logfd:
            log_data = json.dumps({'tag': tag, 'depth': depth, 'time': time.strftime("%Y-%m-%d %H:%M:%S"), 'data': data}, default=self._dumper)
            self.logfd.write(log_data + '\n')
            self.logfd.flush()

    def handle_stacked_log(self):
        # 处理stack中的log
        while self.running_stack:
            # 先取最后一个，记了log之后再pop，避免depth错误
            log_stacked = self.running_stack[-1]
            self.log("function", log_stacked)
            self.running_stack.pop()


def Logwrap(f, logger):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        m = inspect.getcallargs(f, *args, **kwargs)
        fndata = {'name': f.__name__, 'call_args': m, 'start_time': start}
        logger.running_stack.append(fndata)
        try:
            res = f(*args, **kwargs)
        except Exception as e:
            data = {"traceback": traceback.format_exc(), "end_time": time.time()}
            fndata.update(data)
            fndata.update(logger.extra_log)
            logger.log("error", fndata)
            raise
        else:
            fndata.update({'end_time': time.time(), 'ret': res})
            fndata.update(logger.extra_log)
            logger.log('function', fndata)
        finally:
            logger.running_stack.pop()
            logger.extra_log = {}
        return res
    return wrapper
