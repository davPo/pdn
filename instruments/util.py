# -*- coding: utf-8 -*-
"""
    pyvisa.util
    ~~~~~~~~~~~

    General utility functions.

    This file is part of PyVISA.

    :copyright: (c) 2014 by the PyVISA authors.
    :license: MIT, see COPYING for more details.
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import io
import os
import re
import sys
import struct
import subprocess
import contextlib
import platform
import warnings

#from . import __version__

if sys.version >= '3':
    _struct_unpack = struct.unpack
else:
    def _struct_unpack(fmt, string):
        return struct.unpack(str(fmt), string)


def warn_for_invalid_kwargs(keyw, allowed_keys):
    for key in keyw.keys():
        if key not in allowed_keys:
            warnings.warn('Keyword argument "%s" unknown' % key, stacklevel=3)


def filter_kwargs(keyw, selected_keys):
    result = {}
    for key, value in keyw.items():
        if key in selected_keys:
            result[key] = value
    return result


def split_kwargs(keyw, self_keys, parent_keys, warn=True):
    self_kwargs = dict()
    parent_kwargs = dict()
    self_keys = set(self_keys)
    parent_keys = set(parent_keys)
    all_keys = self_keys | parent_keys
    for key, value in keyw.items():
        if warn and key not in all_keys:
            warnings.warn('Keyword argument "%s" unknown' % key, stacklevel=3)
        if key in self_keys:
            self_kwargs[key] = value
        if key in parent_keys:
            parent_kwargs[key] = value

    return self_kwargs, parent_kwargs



_ascii_re = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\d*\.\d+)(?:[eE][-+]?\d+)?")


def parse_ascii(bytes_data):
    return [float(raw_value) for raw_value in
            _ascii_re.findall(bytes_data.decode('ascii'))]


def parse_binary(bytes_data, is_big_endian=False, is_single=False, header=b"#"):
    # DPo : added header
    data = bytes_data
    #print (data.encode('hex')) #test
    # look for the header
    hash_sign_position = bytes_data.find(header)
    if hash_sign_position == -1 or len(data) - hash_sign_position < 3:
        raise ValueError('Cound not find valid hash position')
    # resync frame if misaligned
    if hash_sign_position > 0:
        data = data[hash_sign_position+len(header):]
    else :
        data = data[len(header):]
    data_length=ord(data[0:1])*256+ord(data[1:2])  # compute number of bytes in frame
    data = data[2:2+ data_length] # strip the number of bytes and the terminators if any
    # print (data_length) #test
    #print (data.encode('hex')) #test
    if is_big_endian:
        endianess = ">"
    else:
        endianess = "<"
    try:
        if is_single:
            result=list(_struct_unpack(endianess+"%sf" % (data_length//4), data)) #DPo - simpler
        else:
            result=list(_struct_unpack(endianess+"%sd" % (data_length//8), data)) #DPo - simpler
    except struct.error:
        raise ValueError("Binary data itself was malformed")

    return result


