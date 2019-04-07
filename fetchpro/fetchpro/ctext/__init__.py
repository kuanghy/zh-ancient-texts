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
from ..utils import uri_join


log = logging.getLogger(__name__)


class CTextCrawler(BaseCrawler):

    def __init__(self):
        super().__init__("https://ctext.org/")
        self._zhs_page = "https://ctext.org/zhs"
        self._pro_dir = pathlib.Path(__file__).parent.parent.parent.parent

    def parse_text_page(self, url):
        """解析文本内容页面"""
        doc = PyQuery(self.request(url).encode("utf-8"))
        text_list = []
        log.info("parsing %s", url)
        for item in doc('tr td.ctext').items():
            item_html = item.html()
            if not item_html:
                continue
            if not re.search(r'<div.*</p>', item_html):
                log.warning("undesired text: %s", item_html[:20])
                continue
            item_text = PyQuery(item_html).text()
            text_list.append(item_text.strip())
        return text_list

    def parse_contents_page(self, url, book_name):
        """解析书籍目录页面"""
        doc = PyQuery(self.request(url).encode("utf-8"))
        contents = {}
        log.info("parsing %s", url)

        def _extract_contents(element_pattern):
            for item in doc(element_pattern).items():
                a_href = item.attr('href')
                if not a_href.startswith(book_name):
                    log.warning("undesired href: %s", a_href)
                    continue
                contents[item.html()] = uri_join(self.site, a_href)

        for element_pattern in ['#content3 a', '#content2 a']:
            _extract_contents(element_pattern)
            if contents:
                break

        return contents

    def parse_book_and_save_to_json(self, page, data_meta):
        book_name = data_meta.pop("_simple_bookname")
        json_file = self._pro_dir / "data/json/{}.json".format(book_name)

        data = dict(alldata=[], **data_meta)

        contents = self.parse_contents_page(page, book_name)
        if not contents:
            contents = {data_meta["bookname"]: page}

        text_idx = 0
        # contents = {"道德经": "https://ctext.org/dao-de-jing/zhs"}
        for idx, header in enumerate(contents.keys()):
            section_data = {"section": idx, "header": header, "data": []}
            text_page = contents[header]
            sections = self.parse_text_page(text_page)
            if not sections:
                log.warning("%s text is empty", header)
                self.request.cache.pop(text_page)
            for text in sections:
                text_data = {"ID": text_idx, "text": text}
                section_data['data'].append(text_data)
                text_idx += 1
            data['alldata'].append(section_data)

        with open(json_file, 'w') as fp:
            json.dump(data, fp, ensure_ascii=False)

    def start(self, target_page):
        self.pre_request(self.site)
        self.pre_request(self._zhs_page, headers={'Referer': self.site})
        self.request.session.headers.update(self.pre_request.session.headers)

        resp = self.request(target_page, headers={'Referer': self._zhs_page})
        self.request.session.headers.update({'Referer': target_page})

        doc = PyQuery(resp.content)

        book_type = re.search("《(.*)》", doc("#content3 h2").html()).groups()
        book_type = book_type[0] if book_type else None

        block_pattern = re.compile(r"<br */?> *<br */?>")
        for book_block in re.split(block_pattern, doc("#content3").html()):
            b_doc = PyQuery(book_block)
            book_age = b_doc("span.etext.opt b").text()
            for item in b_doc("a").items():
                url = item.attr("href")
                book_name = re.match(r"(.+)/zhs", url)
                if not book_name:
                    continue

                book_name = book_name.groups()[0]
                book_zh_name = item.text()

                data_meta = {
                    "_simple_bookname": book_name,
                    "bookname": book_zh_name,
                    "writer": None,
                    "type": book_type,
                    "age": book_age,
                }

                self.parse_book_and_save_to_json(url, data_meta)
