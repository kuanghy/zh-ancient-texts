# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-17 15:57:47

import logging
from logging.handlers import RotatingFileHandler

from . import config
from ..utils import log
from ..utils.log import TitledSMTPHandler, SystemLogFormatter


def setup_logging(reset=False, enable_file_log=False, enable_smtp_log=False):
    logger = log.setup_logging(reset, config.LOG_FORMAT)
    if not logger:
        return

    # add rotating file log handler
    if enable_file_log and config.ROTATE_LOG_FILE:
        logfile = config.ROTATE_LOG_FILE
        logsize = config.ROTATE_LOG_FILE_MAXSIZE or (5 * 1024 * 1024)
        backups = config.ROTATE_LOG_FILE_BACKUPS or 10
        file_handler = RotatingFileHandler(
            logfile, maxBytes=logsize, backupCount=backups
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            SystemLogFormatter(config.LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S,%f')
        )
        logger.addHandler(file_handler)
        logger.debug(
            "Added rotating file handler, "
            "logfile: %s, logsize: %s, backups: %s",
            file_handler.baseFilename, file_handler.maxBytes,
            file_handler.backupCount
        )

    # add mail log handler for error
    if enable_smtp_log and config.EMAIL_TOADDRS:
        smtp_handler = TitledSMTPHandler(
            mailhost=config.EMAIL_HOST,
            fromaddr="CrawlerMonitor<{}>".format(config.EMAIL_ADDR),
            toaddrs=config.EMAIL_TOADDRS,
            subject="%(name)s Error: %(message)s",
            credentials=(config.EMAIL_ADDR, config.EMAIL_PASSWD)
        )
        smtp_handler.setLevel(logging.ERROR)
        smtp_handler.setFormatter(logging.Formatter(config.ERROR_MAIL_FORMAT))
        logger.addHandler(smtp_handler)

    return logger
