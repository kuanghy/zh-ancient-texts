# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-16 21:13:24

import random
import logging
from importlib import import_module

import requests
from cached_property import cached_property
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import (
    # ConnectionError as RequestConnectionError,
    Timeout as RequestTimeout,
    SSLError as RequestSSLError
)

from ..utils.retry import retry
from . import config
from .throttle import Throttle
from .useragent import UserAgent


log = logging.getLogger(__name__)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

RemoteHostError = type("RemoteHostError", (Exception,), {})


class Requestor(object):

    def __init__(self, user_agent=None, proxy_pool=None, enable_proxy=True,
                 request_delay=None, cache=None, timeout=None):
        self._user_agent = user_agent
        self.proxy_pool = proxy_pool
        self.enable_proxy = enable_proxy
        self.request_delay = request_delay
        self._cache = cache
        self.timeout = timeout or config.HTTP_TIMEOUT

    @cached_property
    def user_agent(self):
        user_agent = self._user_agent or config.HTTP_USER_AGENT or ''
        try:
            return getattr(UserAgent(), user_agent)
        except AttributeError:
            return self._user_agent

    @property
    def proxies(self):
        proxy_pool = self.proxy_pool or config.HTTP_PROXY_POOL
        return random.choice(proxy_pool) if proxy_pool else None

    @cached_property
    def throttle(self):
        delay = self.request_delay or config.HTTP_REQUEST_DELAY
        return Throttle(delay)

    @cached_property
    def cache(self):
        if self._cache:
            return self._cache

        cache_params = config.HTTP_PAGE_CACHE_PARAMS
        if not cache_params:
            return None

        # TODO: 解析 expires 参数

        cache_type = cache_params.pop("type", '')
        cache_class_name = cache_type.title() + "Cache"
        cache_module = import_module(".cache", __package__)
        try:
            cache_class = getattr(cache_module, cache_class_name)
        except AttributeError:
            raise Exception("unsupported cache type: '%s'" % cache_type)
        return cache_class(**cache_params)

    @cached_property
    def _default_headers(self):
        headers = {}
        if self.user_agent:
            headers['User-Agent'] = self.user_agent
        return headers

    @cached_property
    def session(self):
        session = requests.Session()
        session.headers.update(self._default_headers)
        return session

    def _request(self, url, method="GET", **kwargs):
        method = method.lower()
        request_func = getattr(self.session, method)
        kwargs.setdefault("timeout", self.timeout)
        if self.enable_proxy and self.proxies:
            kwargs["proxies"] = self.proxies
        log.info("requesting '%s', method: %s, kwargs: %s", url, method, kwargs)
        try:
            resp = request_func(url, **kwargs)
        except RequestSSLError as e:
            log.warning(e)
            resp = request_func(url, verify=False, **kwargs)
        body = resp.content.decode("utf-8", errors='ignore')
        log.info("%s '%s', response: %s, body summary: %s",
                 method.title(), url, resp, body[:50].replace('\n', ''))
        try:
            resp.raise_for_status()
        except Exception as e:
            if resp.status_code >= 500:
                raise RemoteHostError() from e
            raise
        return body

    @cached_property
    def request(self):
        retry_params = config.HTTP_RETRY_PARAMS.copy()
        retry_params.update({
            "exceptions": (
                # RequestConnectionError,
                RequestTimeout,
                RemoteHostError
            ),
            "logger": log,
        })
        return retry(**retry_params)(self._request)

    def __call__(self, url, method="GET", **kwargs):
        result = None
        if self.cache:
            try:
                result = self.cache[url]
                log.info("Found '%s' result from the cache", url)
                return result
            except KeyError:
                # url is not available in cache
                pass

        # result was not loaded from cache so still need to download
        self.throttle.wait(url)

        result = self.request(url, method="GET", **kwargs)
        if self.cache:
            # save result to cache
            self.cache[url] = result

        return result
