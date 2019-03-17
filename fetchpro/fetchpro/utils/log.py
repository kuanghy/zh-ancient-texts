# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huayong Kuang <kuanghuayong@joinquant.com>
# CreateTime: 2017-11-30 14:56:07 Thursday

import sys
import logging
import datetime
from logging.handlers import SMTPHandler


defualt_logger = logging.getLogger()

info = defualt_logger.info
warn = defualt_logger.warning
warning = defualt_logger.warning
debug = defualt_logger.debug
error = defualt_logger.error
exception = defualt_logger.exception


DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s -  %(message)s'


class ColoredStreamHandler(logging.StreamHandler):
    """带色彩的流日志处理器"""

    C_BLACK = '\033[0;30m'
    C_RED = '\033[0;31m'
    C_GREEN = '\033[0;32m'
    C_BROWN = '\033[0;33m'
    C_BLUE = '\033[0;34m'
    C_PURPLE = '\033[0;35m'
    C_CYAN = '\033[0;36m'
    C_GREY = '\033[0;37m'

    C_DARK_GREY = '\033[1;30m'
    C_LIGHT_RED = '\033[1;31m'
    C_LIGHT_GREEN = '\033[1;32m'
    C_YELLOW = '\033[1;33m'
    C_LIGHT_BLUE = '\033[1;34m'
    C_LIGHT_PURPLE = '\033[1;35m'
    C_LIGHT_CYAN = '\033[1;36m'
    C_WHITE = '\033[1;37m'

    C_RESET = "\033[0m"

    def __init__(self, *args, **kwargs):
        self._colors = {logging.DEBUG: self.C_DARK_GREY,
                        logging.INFO: self.C_RESET,
                        logging.WARNING: self.C_BROWN,
                        logging.ERROR: self.C_RED,
                        logging.CRITICAL: self.C_LIGHT_RED}
        super(ColoredStreamHandler, self).__init__(*args, **kwargs)

    @property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(message)
            else:
                message = self._colors[record.levelno] + message + self.C_RESET
                stream.write(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def setLevelColor(self, logging_level, escaped_ansi_code):
        self._colors[logging_level] = escaped_ansi_code


class TitledSMTPHandler(SMTPHandler):
    """可定制邮件主题 SMTP 日志处理器"""

    def __init__(self, *args, **kwargs):
        self.linefeed = "\r\n"
        super(TitledSMTPHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        record.host = __import__("socket").gethostname()
        record.user = __import__("getpass").getuser()
        super(TitledSMTPHandler, self).emit(record)

    def getSubject(self, record):
        message = record.getMessage()
        record = vars(record)
        record["message"] = message.strip().split('\n')[-1][:60]
        return self.subject % record


class SystemLogFormatter(logging.Formatter):
    """支持微秒的日志格式器"""

    converter = datetime.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


def setup_logging(reset=False, log_format=None):
    logger = logging.getLogger()

    if len(logger.handlers) > 0 and not reset:
        defualt_logger.debug("logging has been set up")
        return

    # empty handlers
    logger.handlers = []

    logger.setLevel(logging.DEBUG)

    # add stream log handler for info
    if not log_format:
        log_format = DEFAULT_LOG_FORMAT
    stream_handler = ColoredStreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(
        SystemLogFormatter(log_format, datefmt='%Y-%m-%d %H:%M:%S,%f')
    )
    logger.addHandler(stream_handler)

    return logger
