# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-11 13:09:32

import os
import re
import zlib
import shutil
import pathlib
import tempfile
from urllib import parse as urlparse
from os.path import join as path_join
try:
    import cPickle as pickle
except ImportError:
    import pickle

from ..utils import when, cipher
from ..utils.when import TimeDelta


class DiskCache:
    """磁盘缓存

    将一个 url 对应的 html 内容缓存到磁盘上
    """

    def __init__(self, cache_dir=None, expires=None, compress=True):
        self._cache_dir = cache_dir
        self.expires = expires or TimeDelta(days=(500 * 365))
        self.compress = compress

    @property
    def cache_dir(self):
        if self._cache_dir:
            return self._cache_dir
        return path_join(tempfile.gettempdir(), "crawler_cache")

    def __getitem__(self, url):
        path = self.get_cache_path(url)
        if not os.path.exists(path):
            # URL has not yet been cached
            raise KeyError("'{}' page cache does not exist".format(url))
        data = self._get_data(path)
        timestamp = data["timestamp"]
        if self.has_expired(timestamp):
            raise KeyError("'{}' cache has expired".format(url))
        return data["content"]

    def _get_data(self, path):
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as fp:
            data = fp.read()
            if self.compress:
                data = zlib.decompress(data)
            data = pickle.loads(data)
        return data

    def __setitem__(self, url, content):
        data = pickle.dumps({
            "url": url,
            "content": content,
            "timestamp": when.now(),
        })
        path = self.get_cache_path(url)
        self._save_data(path, data)

    def _save_data(self, path, data):
        if self.compress:
            data = zlib.compress(data)
        with open(path, 'wb') as fp:
            fp.write(data)

    def __delitem__(self, url):
        path = pathlib.Path(self.get_cache_path(url))
        os.remove(path)
        try:
            os.removedirs(path.parent)
            os.removedirs(path.parent.parent)
        except OSError:
            pass

    def get_cache_path(self, url):
        url_md5 = cipher.md5(url)
        cache_dir = path_join(self.cache_dir, url_md5[:2], url_md5[-2:])
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return path_join(cache_dir, url_md5)

    def url_to_path(self, url):
        """Create file system path for this URL"""
        components = urlparse.urlsplit(url)
        # when empty path set to /index.html
        path = components.path
        if not path:
            path = '/index.html'
        elif path.endswith('/'):
            path += 'index.html'
        filename = components.netloc + path + components.query
        # replace invalid characters
        filename = re.sub('[^/0-9a-zA-Z\-.,;_ ]', '_', filename)
        # restrict maximum number of characters
        filename = '/'.join(segment[:255] for segment in filename.split('/'))
        return path_join(self.cache_dir, filename)

    def has_expired(self, timestamp):
        return when.now() > timestamp + self.expires

    def pop(self, url):
        content = self[url]
        del self[url]
        return content

    def clear(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)


class SqliteCache(object):

    pass
