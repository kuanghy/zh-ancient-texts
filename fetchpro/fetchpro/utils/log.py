# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huayong Kuang <kuanghuayong@joinquant.com>
# CreateTime: 2017-11-30 14:56:07 Thursday

import sys
import datetime
import logging
from logging.handlers import RotatingFileHandler, BufferingHandler

from . import config


defualt_logger = logging.getLogger()


info = defualt_logger.info
warn = defualt_logger.warning
warning = defualt_logger.warning
debug = defualt_logger.debug
error = defualt_logger.error
exception = defualt_logger.exception


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


class SMTPHandler(logging.Handler):

    def __init__(self, mailhost, fromaddr, toaddrs, subject,
                 credentials=None, secure=None, timeout=5.0):
        logging.Handler.__init__(self)
        if isinstance(mailhost, (list, tuple)):
            self.mailhost, self.mailport = mailhost
        else:
            self.mailhost, self.mailport = mailhost, None
        if isinstance(credentials, (list, tuple)):
            self.username, self.password = credentials
        else:
            self.username = None
        self.fromaddr = fromaddr
        if isinstance(toaddrs, str):
            toaddrs = [toaddrs]
        self.toaddrs = toaddrs
        self.subject = subject
        self.secure = secure
        self.timeout = timeout

    def getSubject(self, record):
        """
        Determine the subject for the email.
        If you want to specify a subject line which is record-dependent,
        override this method.
        """
        return self.subject

    def emit(self, record):
        """
        Emit a record.
        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            from email.message import EmailMessage
            import email.utils

            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port, timeout=self.timeout)
            msg = EmailMessage()
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Subject'] = self.getSubject(record)
            msg['Date'] = email.utils.localtime()
            msg.set_content(self.format(record))
            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.send_message(msg)
            smtp.quit()
        except Exception:
            self.handleError(record)


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
        record = vars(record)
        message = record.getMessage()
        record["message"] = message.strip().split('\n')[-1][:60]
        return self.subject % record


class BufferingSMTPHandler(logging.handlers.BufferingHandler):
    def __init__(self, mailhost, fromaddr, toaddrs, subject, capacity, timelimit):
        logging.handlers.BufferingHandler.__init__(self, capacity)
        self.mailhost = mailhost
        self.mailport = None
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))


class BufferingSMTPHandler(BufferingHandler):

    def __init__(self, capacity, toaddrs=None, subject=None):
        logging.handlers.BufferingHandler.__init__(self, capacity)

        if toaddrs:
            self.toaddrs = toaddrs
        else:
            # Send messages to site administrators by default
            self.toaddrs = zip(*settings.ADMINS)[-1]

        if subject:
            self.subject = subject
        else:
            self.subject = 'logging'

    def flush(self):
        if len(self.buffer) == 0:
            return

        try:
            msg = "\r\n".join(map(self.format, self.buffer))
            emsg = EmailMessage(self.subject, msg, to=self.toaddrs)
            emsg.send()
        except Exception:
            # handleError() will print exception info to stderr if logging.raiseExceptions is True
            self.handleError(record=None)
        self.buffer = []


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


def setup_logging(reset=False):
    logger = logging.getLogger()

    if len(logger.handlers) > 0 and not reset:
        defualt_logger.debug("logging has been set up")
        return

    # empty handlers
    logger.handlers = []

    logger.setLevel(logging.DEBUG)

    # add stream log handler for info
    stream_handler = ColoredStreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(
        SystemLogFormatter(config.LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S,%f'))
    if not enable_extra_log:
        stream_handler.addFilter(JQArenaFilter())
    logger.addHandler(stream_handler)

    # add rotating file log handler
    if enable_file_log and config.ROTATE_LOG_FILE:
        logfile = config.ROTATE_LOG_FILE
        logsize = config.ROTATE_LOG_FILE_MAXSIZE or (5 * 1024 * 1024)
        backups = config.ROTATE_LOG_FILE_BACKUPS or 10
        file_handler = RotatingFileHandler(logfile, maxBytes=logsize, backupCount=backups)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            SystemLogFormatter(config.LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S,%f'))
        if not enable_extra_log:
            file_handler.addFilter(JQArenaFilter())
        logger.addHandler(file_handler)
        logger.debug("Added rotating file handler, logfile: %s, logsize: %s, backups: %s",
                     file_handler.baseFilename, file_handler.maxBytes, file_handler.backupCount)

    # add mail log handler for error
    if enable_smtp_log and config.EMAIL_TOADDRS:
        smtp_handler = TitledSMTPHandler(
            mailhost=config.EMAIL_HOST,
            fromaddr="JQArenaErrorMonitor<{}>".format(config.EMAIL_ADDR),
            toaddrs=config.EMAIL_TOADDRS,
            subject="%(name)s Error: %(message)s",
            credentials=(config.EMAIL_ADDR, config.EMAIL_PASSWD)
        )
        smtp_handler.setLevel(logging.ERROR)
        smtp_handler.setFormatter(logging.Formatter(config.ERROR_MAIL_FORMAT))
        logger.addHandler(smtp_handler)
