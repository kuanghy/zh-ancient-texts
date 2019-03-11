# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-11 13:12:54

import time
import random
import logging
from urllib.parse import urlparse

from ..utils import when


log = logging.getLogger(__name__)


class Throttle(object):
    """请求同一域名时通过休眠来控制页面下载速率"""

    def __init__(self, delay):
        self._delay = delay
        self.domains = {}

    @property
    def delay(self):
        if callable(self._delay):
            _delay = self._delay()
        elif isinstance(self._delay, (tuple, list)):
            _delay = random.uniform(*self._delay)
        else:
            _delay = self._delay
        return _delay

    def wait(self, url):
        domain = urlparse(url).netloc
        last_accessed = self.domains.get(domain)
        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (when.now() - last_accessed).seconds
            if sleep_secs > 0:
                log.info("throttling, wait %ss", sleep_secs)
                time.sleep(sleep_secs)
        self.domains[domain] = when.now()
