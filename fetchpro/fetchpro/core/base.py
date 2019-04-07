# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-11 00:33:08

import re
from urllib import robotparser

import requests
from builtwith import builtwith
from whois import whois
from cached_property import cached_property

from ..utils import uri_join
from .request import Requestor
from .cache import NullCache


class BaseCrawler(object):
    """爬虫基类

    爬取指定站点页面，包含站点抓取前的一些调研工作，如检查 robots.txt，检查站点地图
    识别网站所用技术，寻找网站所有者

    初始化参数：
    ---------
        site: 要爬取的站点，如果为域名则默认为使用 http 协议，也可指定协议，
              如：https://baidu.com
    """

    def __init__(self, site=None):
        self._site = site
        self.request = Requestor()

    @cached_property
    def site(self):
        _site = self._site
        if not _site:
            return None
        return _site if _site.startswith("http") else "http://{}".format(_site)

    @cached_property
    def pre_request(self):
        return Requestor(
            enable_proxy=False,
            request_delay=(1, 3),
            cache=NullCache()
        )

    @property
    def robots_url(self):
        return uri_join(self.site, "/robots.txt") if self.site else None

    @property
    def sitemap_url(self):
        return uri_join(self.site, "/sitemap.xml") if self.site else None

    @cached_property
    def builtwith(self):
        """网站所用技术"""
        return builtwith(self.site)

    def show_builtwith(self):
        print("Site '{}' builtwith message:".format(self.site))
        self.__print_dict_items(self.builtwith)

    @cached_property
    def whois(self):
        """网站所有信息"""
        return whois(self.site)

    def show_whois(self):
        print("Site '{}' owner message:".format(self.site))
        self.__print_dict_items(self.whois)

    @staticmethod
    def __print_dict_items(dct):
        for key, value in dct.items():
            value = "; ".join(value) if isinstance(value, (list, tuple, set)) else value
            print("  - {key}: {value}".format(key=key, value=value))

    def fetch_robots(self):
        """抓取 robots.txt 文件，返回 urllib.robotsparser.RobotsFileParser 对象"""
        rp = robotparser.RobotFileParser()
        rp.set_url(self.robots_url)
        rp.read()
        return rp

    def fetch_sitemap(self):
        """获取站点地图

        默认解析 xml 格式的站点地图，如需解析其他格式可在子类重写该方法
        """
        req = requests.get(self.sitemap_url)
        return re.findall(r"<loc>(.*?)</loc>", req.text)
