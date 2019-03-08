#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-08 20:34:35

import re
import json
import requests
from pyquery import PyQuery


def parse_text_page(url):
    """解析文本内容页面"""
    resp = requests.get(url)
    doc = PyQuery(resp.content)
    text_list = []
    for item in doc('tr td.ctext').items():
        item_html = item.html()
        if not re.search(r'<div.*</p>', item_html):
            continue
        item_text = PyQuery(item_html).text()
        text_list.append(item_text.strip())

    return text_list


def parse_contents_page(url, book_name):
    """解析书籍目录页面"""
    resp = requests.get(url)
    doc = PyQuery(resp.content)
    contents = {}
    for item in doc('#content3 a').items():
        a_href = item.attr('href')
        if not a_href.startswith(book_name):
            continue
        contents[item.html()] = "https://ctext.org/" + a_href
    return contents


def main():
    json_file = "../data/json/huangdi-neijing-suwen.json"
    content_page = "https://ctext.org/huangdi-neijing/suwen/zhs"
    data = {
        "bookname" : "黄帝内经",
        "writer" : "黄帝，歧伯",
        "type" : "医书",
        "age" : "中古",
        "alldata" : []
    }
    contents = parse_contents_page(content_page, 'huangdi-neijing')
    text_idx = 0
    for idx, header in enumerate(contents.keys()):
        section_data = {"section": idx, "header": header, "data": []}
        text_page = contents[header]
        for text in parse_text_page(text_page):
            text_data = {"ID": text_idx, "text": text}
            section_data['data'].append(text_data)
            text_idx += 1
        data['alldata'].append(section_data)

    print(data)
    with open(json_file, 'w') as fp:
        json.dump(data, fp)


if __name__ == "__main__":
    main()
