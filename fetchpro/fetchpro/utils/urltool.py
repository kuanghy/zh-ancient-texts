# -*- coding: utf-8 -*-

# Copyright (c) Huoty, All rights reserved
# Author: Huoty <sudohuoty@gmail.com>
# CreateTime: 2019-03-17 18:47:23


def uri_join(*args, **kwargs):
    if not args:
        return None
    if len(args) == 1:
        return args[0]

    encoding = kwargs.get("encoding", "utf-8")

    is_all_bytes = True
    uri_list = []
    last_idx = len(args) - 1
    for idx, uri in enumerate(args):
        if isinstance(uri, bytes):
            uri = uri.decode(encoding)
        elif isinstance(uri, str):
            is_all_bytes = False
        else:
            raise ValueError("unsupported type '%s'" % type(uri))

        if idx == 0:
            uri = uri.rstrip('/')
        elif idx == last_idx:
            uri = uri.lstrip('/')
        else:
            uri = uri.strip('/')
        uri_list.append(uri)

    new_uri = '/'.join(uri_list)
    if is_all_bytes:
        new_uri = new_uri.encode(encoding)
    return new_uri
