#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-08 20:34:35

import os
import re
import json
import time
import random
import logging
import logging as log

import requests
from pyquery import PyQuery


session = requests.Session()
session.headers["User-Agent"] = " ".join([
    "Mozilla/5.0",
    "(Windows NT 10.0; Win64; x64)",
    "AppleWebKit/537.36",
    "(KHTML, like Gecko)",
    "Chrome/67.0.3396.99 Safari/537.36",
])


def random_time_sleep():
    time.sleep(random.uniform(30, 180))


def parse_text_page(url):
    """解析文本内容页面"""
    resp = session.get(url)
    doc = PyQuery(resp.content)
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


def parse_contents_page(url, book_name):
    """解析书籍目录页面"""
    resp = session.get(url)
    doc = PyQuery(resp.content)
    contents = {}
    log.info("parsing %s", url)
    for item in doc('#content3 a').items():
        a_href = item.attr('href')
        if not a_href.startswith(book_name):
            log.warning("undesired href: %s", a_href)
            continue
        contents[item.html()] = "https://ctext.org/" + a_href
    return contents


def main():
    session.get("https://ctext.org/")
    random_time_sleep()
    session.headers["Referer"] = "https://ctext.org/"
    session.get("https://ctext.org/zhs")
    random_time_sleep()
    session.headers["Referer"] = "https://ctext.org/zhs"
    session.get("https://ctext.org/pre-qin-and-han/zhs")
    random_time_sleep()
    session.headers["Referer"] = "https://ctext.org/pre-qin-and-han/zhs"
    session.get("https://ctext.org/huangdi-neijing/zhs")
    random_time_sleep()
    session.headers["Referer"] = "https://ctext.org/huangdi-neijing/zhs"
    session.get("https://ctext.org/huangdi-neijing/suwen/zhs")
    random_time_sleep()
    session.headers["Referer"] = "https://ctext.org/huangdi-neijing/suwen/zhs"

    json_file = "../data/json/huangdi-neijing-suwen.json"
    content_page = "https://ctext.org/huangdi-neijing/suwen/zhs"
    data = {
        "bookname": "黄帝内经",
        "writer": "黄帝，歧伯",
        "type": "医书",
        "age": "中古",
        "alldata": []
    }
    if os.path.exists(json_file):
        with open(json_file) as fp:
            data = json.load(fp)
    contents = parse_contents_page(content_page, 'huangdi-neijing')
    text_idx = 0
    # for idx, header in enumerate(contents.keys()):
    for section_data in data["alldata"]:
        # section_data = {"section": idx, "header": header, "data": []}
        header = section_data["header"]
        if len(section_data["data"]):
            log.info("section '%s' is exists", header)
            continue
        text_page = contents[header]
        sections = parse_text_page(text_page)
        if not sections:
            log.warning("%s text is empty", header)
        for text in sections:
            text_data = {"ID": text_idx, "text": text}
            section_data['data'].append(text_data)
            text_idx += 1
            random_time_sleep()
        data['alldata'].append(section_data)

    with open(json_file, 'w') as fp:
        json.dump(data, fp)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s -  %(message)s'
    )
    main()
