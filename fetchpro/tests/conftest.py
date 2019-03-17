# -*- coding: utf-8 -*-

import os
import sys
import glob
import warnings
import itertools

try:
    import pycodestyle
except ImportError:
    pycodestyle = None
    warnings.warn("No pycodestyle module", Warning)


def pytest_addoption(parser):
    parser.addoption("--full-test", action="store_true", help="run full test")
    parser.addoption("--no-check-codestyle", action="store_true",
                     help="disable codestyle checker")


def pytest_sessionstart(session):
    check_codesyle = not session.config.getoption("--no-check-codestyle")
    if check_codesyle and pycodestyle:
        rootdir = str(session.config.rootdir)
        pyfiles = itertools.chain(
            glob.iglob(os.path.join(rootdir, '*.py')),
            glob.iglob(os.path.join(rootdir, '*', '*.py')),
            glob.iglob(os.path.join(rootdir, '*', '*', '*.py'))
        )
        for path in pyfiles:
            # check_file_codestyle(path)
            pass

    import fetchpro.core
    from fetchpro.utils.log import TitledSMTPHandler
    from fetchpro.core.log import setup_logging
    from fetchpro.core.config import load_config

    class MockSMTPHandler(TitledSMTPHandler):

        def emit(self, record):
            import socket
            import getpass
            from email.utils import formatdate
            record.host = socket.gethostname()
            record.user = getpass.getuser()
            msg = self.format(record)
            msg = "From: {}\nTo: {}\nSubject: {}\nDate: {}\n\n{}".format(
                self.fromaddr,
                ",".join(self.toaddrs),
                self.getSubject(record),
                formatdate(),
                msg
            )
            print("{sep_line}\n{msg}\n{sep_line}".format(sep_line=("-" * 80), msg=msg))

    config = load_config()
    config.EMAIL_HOST = "smtp.exmail.qq.com"
    config.EMAIL_ADDR = "xxx@joinquant.com"
    config.EMAIL_PASSWD = "xxxxxx"
    config.EMAIL_TOADDRS = ("yyy@joinquant.com", "zzz@joinquant.com")
    fetchpro.core.log.config = config
    fetchpro.core.log.TitledSMTPHandler = MockSMTPHandler
    setup_logging(enable_smtp_log=True)


def check_file_codestyle(path, ignore=None, max_line_length=100):
    ignore = ['E402', 'E731', 'W503', 'W504'] if ignore is None else ignore
    checker = pycodestyle.Checker(
        filename=str(path),
        ignore=ignore,
        max_line_length=max_line_length,
        show_source=True,
    )
    assert not checker.check_all(), "bad codestyle"
