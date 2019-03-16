# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-16 11:02:19

import time

import pytest

from fetchpro.utils import when
from fetchpro.core.cache import DiskCache


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
