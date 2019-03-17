# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-11 00:30:46

import re
import json
import logging
import pathlib

from pyquery import PyQuery

from ..core import BaseCrawler
from ..core.request import Requestor
from ..core.cache import NullCache
from ..utils import uri_join


log = logging.getLogger(__name__)


class CTextCrawler(BaseCrawler):

    def __init__(self):
        super().__init__("https://ctext.org/")

        self.pre_request = Requestor(request_delay=(1, 3), cache=NullCache())

    def parse_text_page(self, url):
        """解析文本内容页面"""
        doc = PyQuery(self.request(url))
        text_list = []
        log.info("parsing %s", url)
        for item in doc('tr td.ctext').items():
            item_html = item.html()
            if not re.search(r'<div.*</p>', item_html):
                log.warning("undesired text: %s", item_html[:20])
                continue
            item_text = PyQuery(item_html).text()
            text_list.append(item_text.strip())
        return text_list

    def parse_contents_page(self, url, book_name):
        """解析书籍目录页面"""
        doc = PyQuery(self.request(url))
        contents = {}
        log.info("parsing %s", url)
        for item in doc('#content3 a').items():
            a_href = item.attr('href')
            if not a_href.startswith(book_name):
                log.warning("undesired href: %s", a_href)
                continue
            contents[item.html()] = uri_join(self.site, a_href)
        return contents

    def start(self):
        self.pre_request("https://ctext.org/")
        self.pre_request(
            "https://ctext.org/zhs",
            headers={'Referer': 'https://ctext.org/'}
        )
        self.pre_request(
            "https://ctext.org/pre-qin-and-han/zhs",
            headers={'Referer': 'https://ctext.org/zhs'}
        )
        self.pre_request(
            "https://ctext.org/huangdi-neijing/zhs",
            headers={'Referer': 'https://ctext.org/pre-qin-and-han/zhs'}
        )

        self.request.session.update(self.pre_request.session)
        lingshujin_nav_page = "https://ctext.org/huangdi-neijing/ling-shu-jing/zhs"
        self.request(
            lingshujin_nav_page,
            headers={'Referer': 'https://ctext.org/huangdi-neijing/zhs'}
        )

        self.request.session.update({'Referer': lingshujin_nav_page})

        pro_dir = pathlib.Path(__file__).parent.parent.parent
        json_file = pro_dir / "data/json/huangdi-neijing-lingshujin.json"

        data = {
            "bookname": "黄帝内经●灵枢经",
            "writer": "黄帝，歧伯",
            "type": "医书",
            "age": "中古",
            "alldata": []
        }
        # if os.path.exists(json_file):
        #     with open(json_file) as fp:
        #         data = json.load(fp)

        contents = self.parse_contents_page(lingshujin_nav_page, 'huangdi-neijing')
        text_idx = 0
        for idx, header in enumerate(contents.keys()):
            section_data = {"section": idx, "header": header, "data": []}
            text_page = contents[header]
            sections = self.parse_text_page(text_page)
            if not sections:
                log.warning("%s text is empty", header)
            for text in sections:
                text_data = {"ID": text_idx, "text": text}
                section_data['data'].append(text_data)
                text_idx += 1
            data['alldata'].append(section_data)

        with open(json_file, 'w') as fp:
            json.dump(data, fp, ensure_ascii=False)
