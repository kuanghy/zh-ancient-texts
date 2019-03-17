# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2017-06-26 19:38:56 Monday

import time
import math
import random
import logging
import functools


class Retrier(object):
    """重试器

    初始化参数说明：

        attempts: 重试次数, 默认一直重试
        delay: 两次重试之间的间隔时间, 可以为一个 list 或 tuple 来指定每次间隔的时间,
            且重试次数为其长度
        exceptions: 指定哪些异常发生时需要重试, 可以是一个 list 或者 tuple
        exponential, max_delay: 时间间隔按指数增长. 如果 exponential 为 True,
            则每次的时间间隔为：(2 ** previous_tried_count) * delay
            max_delay 表示当增长到该值时不再增长，即超过该值后就永远为该值
        random_delay_min, random_delay_max: 随机间隔时间
        delay_func: 间隔函数, 每次重试会调用该函数产生一个间隔时间,
            调用该函数时会把第几次重试作为参数传入
        logger: 日志系统, 为 None 时不输出信息

    间隔时间的类型优先级为: 函数间隔 > 列表间隔 > 指数间隔 > 随机间隔 > 固定间隔
    即如果指定了 exponential 为 True, 又同时指定了 random_delay_min, random_delay_max,
    则默认采用指数间隔
    """

    def __init__(self, attempts=None, delay=None, exceptions=Exception,
                 exponential=False, max_delay=None,
                 random_delay_min=None, random_delay_max=None,
                 delay_func=None, logger=None):

        if exponential and not isinstance(delay, (int, float)):
            raise TypeError("exponential must be a number")

        self.attempts = int(attempts) if attempts else -1

        if isinstance(delay, (list, tuple)):
            self.delay = delay
            self.attempts = len(self.delay)
        else:
            self.delay = float(delay) if delay else 0

        self.exceptions = (tuple(exceptions) if isinstance(exceptions, list)
                           else exceptions)

        self.exponential = exponential

        self.max_delay = (float(max_delay) if max_delay is not None
                          else float("inf"))

        self.random_delay_min = random_delay_min
        self.random_delay_max = random_delay_max

        self.delay_func = delay_func

        if not logger:
            logger = logging.getLogger("Retrier")
            logger.setLevel(logging.CRITICAL)
        self.log = logger

    @staticmethod
    def _ordinal(num):
        idx = (math.floor(num / 10) % 10 != 1) * (num % 10 < 4) * num % 10
        suffix = "tsnrhtdd"[idx::4]
        return "{}{}".format(num, suffix)

    def calc_delay(self, tried_times):
        if isinstance(self.delay, (list, tuple)):
            return float(self.delay[tried_times])
        elif self.exponential:
            delay = self.delay * (2 ** tried_times)
            return delay if delay < self.max_delay else self.max_delay
        elif self.random_delay_min or self.random_delay_max:
            random_delay_min = (0 if self.random_delay_min is None
                                else float(self.random_delay_min))
            random_delay_max = (1 << 64 if self.random_delay_max is None
                                else float(self.random_delay_min))
            return random.uniform(random_delay_min, random_delay_max)
        else:
            return self.delay

    def call(self, func, *args, **kwargs):
        log = self.log
        attempts = self.attempts
        exceptions = self.exceptions
        tried_count = -1

        while 1:
            try:
                tried_count += 1
                return func(*args, **kwargs)
            except exceptions:
                if attempts == 0:
                    raise

                log.exception("call %s failed, tried_count=%s", func.__name__,
                              tried_count)

                attempts -= 1
                delay = (self.delay_func(tried_count + 1) if self.delay_func
                         else self.calc_delay(tried_count))
                time.sleep(delay)
                log.info("%s try to call %s", self._ordinal(tried_count + 1),
                         func.__name__)


def retry(*dargs, **dkw):
    if len(dargs) == 1 and callable(dargs[0]):

        def wrapper_simple(func):
            @functools.wraps(func)
            def wrapped_func(*args, **kw):
                return Retrier().call(func, *args, **kw)
            return wrapped_func
        return wrapper_simple(dargs[0])

    else:

        def wrapper(func):
            @functools.wraps(func)
            def wrapped_func(*args, **kw):
                return Retrier(*dargs, **dkw).call(func, *args, **kw)
            return wrapped_func
        return wrapper
