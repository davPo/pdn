# -*- coding: utf-8 -*-
"""
    pyvisa.errors
    ~~~~~~~~~~~~~

    Defines exceptions hierarchy and textual explanations of VISA completion and error codes.

    This file is part of PyVISA.

    :copyright: (c) 2014 by the PyVISA authors.
    :license: MIT, see COPYING for more details.
"""


class Error(Exception):
    """Abstract basic exception class for this module."""

    def __init__(self, description):
        super(Error, self).__init__(description)

class UnknownHandler(Error):
    """Exception class for invalid handler data given to uninstall_handler().

    uninstall_handler() checks whether the handler and user_data parameters
    point to a known handler previously installed with install_handler().  If
    it can't find it, this exception is raised.

    """

    def __init__(self, event_type, handler, user_handle):
        super(UnknownHandler, self).__init__('%s, %s, %s' % (event_type, handler, user_handle))


class OSNotSupported(Error):

    def __init__(self, os):
        super(OSNotSupported, self).__init__(os + " is not yet supported by PyVISA")


class InvalidBinaryFormat(Error):

    def __init__(self, description=""):
        if description:
            description = ": " + description
        super(InvalidBinaryFormat, self).__init__("Unrecognized binary data format" + description)

