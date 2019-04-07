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
            if not re.search("""<div *id=['"]comm""", item_html.strip()):
                log.warning("undesired text: %s", item_html[:60])
                continue
            item_text = item.text()
            text_list.append(item_text.strip())
        return text_list

    def parse_contents_page(self, url, book_name):
        """解析书籍目录页面"""
        doc = PyQuery(self.request(url).encode("utf-8"))
        contents = {}
        log.info("parsing %s", url)

        block_pattern = re.compile(r"<br */?> *<br */?>")

        def _extract_contents(element_pattern):
            contents_html = doc(element_pattern).html()
            if not contents_html:
                log.warning("contents html is empty: %s", contents_html)
                return

            contents_blocks = [
                item for item in
                re.split(block_pattern, contents_html)
            ]
            # 如果目录是分块的，说明此书籍是分篇目的
            has_multi_parts = len(contents_blocks) > 1

            for contents_block in contents_blocks:
                b_doc = PyQuery(contents_block)
                sub_name = None
                for item in b_doc("a").items():
                    a_href = item.attr('href')
                    if not a_href.startswith(book_name) or not a_href.endswith("zhs"):
                        log.warning("undesired href: %s", a_href)
                        continue

                    if has_multi_parts:
                        if sub_name is None:
                            # 第一个链接是篇目的标题
                            sub_name = item.html()
                            log.info("'%s' has multiple parts, sub_name: %s",
                                     book_name, sub_name)
                            continue
                        header = "{}●{}".format(sub_name, item.html())
                    else:
                        header = item.html()
                    contents[header] = uri_join(self.site, a_href)

        for element_pattern in ['#content3', '#content2']:
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

        doc = PyQuery(resp.encode("utf-8"))

        book_type = re.search("《(.*)》", doc("#content3 h2").html()).groups()
        book_type = book_type[0] if book_type else None

        block_pattern = re.compile(r"<br */?> *<br */?>")
        for book_block in re.split(block_pattern, doc("#content3").html()):
            b_doc = PyQuery(book_block)
            book_age = b_doc("span.etext.opt b").text()
            for item in b_doc("a").items():
                url = item.attr("href")
                book_name = re.match(r"([^/]+)/zhs", url)
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
                log.info("get '%s' data meta: %s", book_name, data_meta)

                book_contents_page = uri_join(self.site, url)
                self.parse_book_and_save_to_json(book_contents_page, data_meta)
