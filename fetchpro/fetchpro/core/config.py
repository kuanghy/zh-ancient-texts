# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-16 17:40:01

import os
import pathlib
import logging
import warnings


# 邮件发送配置，配置时会发送错误日志报告邮件，否则不发送
EMAIL_HOST = ""       # 发件邮箱 SMTP 服务器
EMAIL_ADDR = ""       # 发件邮箱地址
EMAIL_PASSWD = ""     # 发件邮箱密码
EMAIL_TOADDRS = []    # 收件人列表


# 日志相关配置
ROTATE_LOG_FILE = None
ROTATE_LOG_FILE_MAXSIZE = None
ROTATE_LOG_FILE_BACKUPS = None

LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
ERROR_MAIL_FORMAT = """\
Logger Name:        %(name)s
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Host:               %(host)s
User:               %(user)s
Time:               %(asctime)s

Message:

%(message)s
"""


class Config(object):

    def __new__(cls, path=None):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.initialize(path)
        return cls._instance

    def initialize(self, path=None):
        self._log = logging.getLogger(__name__)

        self.__cfg__ = globals()

        this_dir = pathlib.Path(__file__).parent
        config_paths = (
            (this_dir.parent.parent / "config.py"),
            path
        )

        for path in config_paths:
            self.__load_config(path, self.__cfg__)

        if not self.__cfg__["SSDB_URLS"] and self.__cfg__["SSDB_URL"]:
            self.__cfg__["SSDB_URLS"] = [self.__cfg__["SSDB_URL"]]

    def __load_config(self, path, scope):
        if not path or not os.path.exists(path):
            return

        self._log.debug("Load config: %s", path)
        with open(path) as f:
            code = compile(f.read(), path, "exec")
            exec(code, scope, scope)

    def __getattr__(self, name):
        try:
            return self.__cfg__[name]
        except KeyError:
            warnings.warn("No config '%s'" % name, Warning)
            return None


def load_config(path=None):
    return Config(path)
