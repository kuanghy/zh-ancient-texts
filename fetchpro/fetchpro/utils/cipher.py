# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-16 10:21:43

import hashlib


def md5(content, encoding='utf-8'):
    if isinstance(content, str):
        content = content.encode(encoding)
    return hashlib.md5(content).hexdigest()


def sha1(content, encoding='utf-8'):
    if isinstance(content, str):
        content = content.encode(encoding)
    return hashlib.sha1(content).hexdigest()
