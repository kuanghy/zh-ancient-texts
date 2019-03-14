# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-11 00:35:50


def uri_join(*args):
    if not args:
        return None
    if len(args) == 1:
        return args[0]
    args = [
        [args[0].rstrip('/')] +
        [uri.strip('/') for uri in args[1:-1]] +
        [args[-1].lstrip('/')]
    ]
    return '/'.join(args)
