# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-11 20:39:27

import re
import datetime
from contextlib import suppress


DateTime = datetime.datetime
Date = datetime.date
Time = datetime.time
TimeDelta = datetime.timedelta

today = datetime.date.today
now = datetime.datetime.now

MAX_DATE = datetime.date.max
MIN_DATE = datetime.date.min

MAX_DT = datetime.datetime.max
MIN_DT = datetime.datetime.min

MAX_TD = datetime.timedelta.max
MIN_TD = datetime.timedelta.min


def date2str(date, separator=None):
    if not isinstance(date, Date):
        raise ValueError("date must be datetime.date")
    separator = separator if separator else ""
    style = separator.join(["%Y", "%m", "%d"])
    return date.strftime(style)


def date2dt(date):
    """Convert datetime.date to datetime.datetime"""
    return DateTime.combine(date, Time.min)


def convert_date(date):
    """转换多种日期类型为 datetime.date 类型"""
    if isinstance(date, __import__("pandas").Timestamp):
        date = str(date)

    if isinstance(date, str):
        if ':' in date:
            date = date[:10]
        with suppress(ValueError):
            return Date(*map(int, date.split('-')))
    elif isinstance(date, datetime.datetime):
        return date.date()
    elif isinstance(date, datetime.date):
        return date
    raise ValueError("date must be datetime.date, datetime.datetime, "
                     "pandas.Timestamp or as '2015-01-05'")


def convert_dt(dt):
    """Convert anything to datetime.datetime"""
    if isinstance(dt, str):
        with suppress(ValueError):
            return DateTime(*map(int, re.split(r"\W+", dt)))
    elif isinstance(dt, DateTime):
        return dt
    elif isinstance(dt, Date):
        return date2dt(dt)
    raise ValueError("dt must be datetime.date, datetime.datetime or "
                     "as '2015-01-05 12:00:00'")


def parse_date(s):
    """解析日期为 datetime.date 类型"""
    if isinstance(s, datetime.datetime):
        return s.date()
    if isinstance(s, datetime.date):
        return s
    if isinstance(s, str):
        if '-' in s:
            return datetime.datetime.strptime(s, "%Y-%m-%d").date()
        else:
            return datetime.datetime.strptime(s, "%Y%m%d").date()
    if isinstance(s, int):
        return datetime.date(year=s // 10000,
                             month=(s // 100) % 100,
                             day=s % 100)
    raise ValueError("Unknown {} for parse_date.".format(s))


def convert_timestamp(dt):
    dt = convert_dt(dt)
    return dt.timestamp()
