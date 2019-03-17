# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-16 11:02:19

import os
import time
import logging
import tempfile

import pytest

from fetchpro.utils import when
from fetchpro.core import config
from fetchpro.core.cache import DiskCache
from fetchpro.core.request import Requestor
from fetchpro.core.useragent import UserAgent
from fetchpro.core.log import setup_logging, RotatingFileHandler
from fetchpro.utils.log import ColoredStreamHandler, TitledSMTPHandler


class TestDiskCache(object):

    def setup_class(cls):
        cls.cache = DiskCache(expires=when.TimeDelta(seconds=1))

    def teardown_class(cls):
        cls.cache.clear()

    def test_cache(self):
        url = "http://baidu.com"
        content = "<h1>hello world!</h1>"
        self.cache[url] = content
        assert self.cache[url] == content

        time.sleep(self.cache.expires.seconds)
        with pytest.raises(KeyError):
            self.cache["url"]

        cache_path = self.cache.get_cache_path(url)
        cache_data = self.cache._get_data(cache_path)
        assert len(cache_data) == 3
        assert cache_data["content"] == content


class TestRequestor(object):

    def setup_class(cls):
        cls.request = Requestor(request_delay=1)

    def teardown_class(cls):
        if cls.request.cache:
            cls.request.cache.clear()

    def test_request(self):
        ua = UserAgent()

        assert self.request.user_agent == ua.chrome
        assert not self.request.proxies

        assert self.request("https://www.baidu.com")
        assert self.request("https://www.baidu.com")
        assert self.request("https://www.baidu.com/duty/")
        assert self.request("http://news.baidu.com")


class TestLog(object):

    def setup_class(self):
        pass

    @staticmethod
    def group_log(log):
        log.info("This is info")
        log.debug("This is debug")
        log.warning("This is warning")
        log.error("This is error")
        try:
            1/0
        except Exception as e:
            log.exception(e)

    def test_get_logger(self):
        log = logging.getLogger("TestLogger")
        self.group_log(log)

    def test_get_rotating_logger(self):
        rotate_log_file = config.ROTATE_LOG_FILE
        config.ROTATE_LOG_FILE = None
        setup_logging(reset=True)
        log = logging.getLogger("TestLogger.JQArena.Rotating")
        self.group_log(log)

        log = logging.getLogger()
        assert len(log.handlers) == 1

        config.ROTATE_LOG_FILE = rotate_log_file

    def test_get_rotating_logger2(self):
        logfile = tempfile.mkstemp(suffix=".log")[1]

        config.ROTATE_LOG_FILE = logfile
        config.ROTATE_LOG_FILE_MAXSIZE = 20 * 1024 * 1024
        config.ROTATE_LOG_FILE_BACKUPS = 10
        setup_logging(reset=True, enable_file_log=True)
        log = logging.getLogger("TestLogger.Rotating")

        self.group_log(log)

        log = logging.getLogger()
        for handler in log.handlers:
            assert isinstance(handler, (ColoredStreamHandler, RotatingFileHandler))

            if isinstance(handler, RotatingFileHandler):
                assert handler.maxBytes == 20 * 1024 * 1024
                assert handler.backupCount == 10

        assert open(logfile).read()
        os.remove(logfile)

        config.ROTATE_LOG_FILE = None
        setup_logging(reset=True)

    @pytest.mark.skipif(not os.getenv("FULL_TEST"), reason="full test only")
    def test_get_reported_logger(self):
        old_email_toaddrs = config.EMAIL_TOADDRS
        config.EMAIL_TOADDRS = ["huayongkuang@qq.com"]
        setup_logging(reset=True, enable_smtp_log=True)
        log = logging.getLogger("TestLogger.Reported")

        for handler in log.handlers:
            assert isinstance(handler, (ColoredStreamHandler, TitledSMTPHandler))

        self.group_log(log)

        config.EMAIL_TOADDRS = old_email_toaddrs
        setup_logging(reset=True)
