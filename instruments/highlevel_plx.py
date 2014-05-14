# -*- coding: utf-8 -*-
"""
    plx.highlevel
    ~~~~~~~~~~~~~~~~

    High level PyVisa like for Ethernet Prologix.
"""

import time
import atexit
import warnings
from collections import defaultdict

from . import logger
from .constants import *
from . import ctwrapper
from . import errors
from .util import (warning_context, split_kwargs, warn_for_invalid_kwargs,
                   parse_ascii, parse_binary, get_library_paths)


# The bits in the bitfield mean the following:
#
# bit number   if set / if not set
#     0          binary/ascii
#     1          double/single (IEEE floating point)
#     2          big-endian/little-endian
#
# This leads to the following constants:

ascii      = 0
single     = 1
double     = 3
big_endian = 4

CR = '\r'
LF = '\n'


class GpibInstrument(object):
    """Class for all kinds of Instruments.

    It can be instantiated, however, if you want to use special features of a
    certain interface system (GPIB, USB, RS232, etc), you must instantiate one
    of its child classes.

    :param resource_name: the instrument's resource name or an alias,
                          may be taken from the list from
                          `list_resources` method from a ResourceManager.
    :param timeout: the VISA timeout for each low-level operation in
                    milliseconds.
    :param term_chars: the termination characters for this device.
    :param chunk_size: size of data packets in bytes that are read from the
                       device.
    :param lock: whether you want to have exclusive access to the device.
                 Default: VI_NO_LOCK
    :param ask_delay: waiting time in seconds after each write command.
                      Default: 0.0
    :param send_end: whether to assert end line after each write command.
                     Default: True
    :param values_format: floating point data value format. Default: ascii (0)
    """

    #: Termination character sequence.
    __term_chars = None


    DEFAULT_KWARGS = {#: Termination character sequence.
                      'term_chars': None,
                      #: How many bytes are read per low-level call.
                      'chunk_size': 20 * 1024,
                      #: Seconds to wait between write and read operations inside ask.
                      'ask_delay': 0.0,
                      'send_end': True,
                      #: floating point data value format
                      'values_format': ascii}

    ALL_KWARGS = dict(DEFAULT_KWARGS)

    def __init__(self, resource_name, **kwargs):
        skwargs, pkwargs = split_kwargs(kwargs,GpibInstrument.DEFAULT_KWARGS.keys())

        super(GpibInstrument, self).__init__(resource_name,  **pkwargs)

        for key, value in GpibInstrument.DEFAULT_KWARGS.items():
            setattr(self, key, skwargs.get(key, value))

    def write_raw(self, message):
        """Write a string message to the device.

        The term_chars are appended to it, unless they are already.

        :param message: the message to be sent.
        :type message: bytes
        :return: number of bytes written.
        :rtype: int
        """

        return self.visalib.write(self.session, message)

    def write(self, message):
        """Write a string message to the device.

        The term_chars are appended to it, unless they are already.

        :param message: the message to be sent.
        :type message: unicode (Py2) or str (Py3)
        :return: number of bytes written.
        :rtype: int
        """

        if self.__term_chars and not message.endswith(self.__term_chars):
            message += self.__term_chars
        elif self.__term_chars is None and not message.endswith(CR + LF):
            message += CR + LF

        count = self.write_raw(message.encode('ascii'))

        return count

    def _strip_term_chars(self, message):
        """Strips termination chars from a message

        :type message: str
        """
        if self.__term_chars:
            if message.endswith(self.__term_chars):
                message = message[:-len(self.__term_chars)]
            else:
                warnings.warn("read string doesn't end with "
                              "termination characters", stacklevel=2)

        return message.rstrip(CR + LF)

    def read_raw(self):
        """Read the unmodified string sent from the instrument to the computer.

        In contrast to read(), no termination characters are checked or
        stripped. You get the pristine message.

        :rtype: bytes

        """
        ret = bytes()
        with warning_context("ignore", "VI_SUCCESS_MAX_CNT"):
            try:
                status = VI_SUCCESS_MAX_CNT
                while status == VI_SUCCESS_MAX_CNT:
                    logger.debug('Reading %d bytes from session %s (last status %r)',
                                 self.chunk_size, self.session, status)
                    ret += self.visalib.read(self.session, self.chunk_size)
                    status = self.visalib.status
            except errors.VisaIOError as e:
                logger.debug('Exception while reading: %s', e)
                raise

        return ret

    def read(self):
        """Read a string from the device.

        Reading stops when the device stops sending (e.g. by setting
        appropriate bus lines), or the termination characters sequence was
        detected.  Attention: Only the last character of the termination
        characters is really used to stop reading, however, the whole sequence
        is compared to the ending of the read string message.  If they don't
        match, a warning is issued.

        All line-ending characters are stripped from the end of the string.

        :rtype: str
        """

        return self._strip_term_chars(self.read_raw().decode('ascii'))

    def read_values(self, fmt=None):
        """Read a list of floating point values from the device.

        :param fmt: the format of the values.  If given, it overrides
            the class attribute "values_format".  Possible values are bitwise
            disjunctions of the above constants ascii, single, double, and
            big_endian.  Default is ascii.

        :return: the list of read values
        :rtype: list
        """
        if not fmt:
            fmt = self.values_format

        if fmt & 0x01 == ascii:
            return parse_ascii(self.read())

        data = self.read_raw()

        try:
            if fmt & 0x01 == single: #DPO FIXME
                is_single = True
            elif fmt & 0x03 == double:
                is_single = False
            else:
                raise ValueError("unknown data values fmt requested")
            return parse_binary(data, fmt & 0x04 == big_endian, is_single,header=b"#A")
        except ValueError as e:
            raise errors.InvalidBinaryFormat(e.args)

    def ask(self, message, delay=None):
        """A combination of write(messa1e) and read()

        :param message: the message to send.
        :type message: str
        :param delay: delay in seconds between write and read operations.
                      if None, defaults to self.ask_delay
        :returns: the answer from the device.
        :rtype: str
        """

        self.write(message)
        if delay is None:
            delay = self.ask_delay
        if delay > 0.0:
            time.sleep(delay)
        return self.read()

    def ask_for_values(self, message, format=None, delay=None):
        """A combination of write(message) and read_values()

        :param message: the message to send.
        :type message: str
        :param delay: delay in seconds between write and read operations.
                      if None, defaults to self.ask_delay
        :returns: the answer from the device.
        :rtype: list
        """

        self.write(message)
        if delay is None:
            delay = self.ask_delay
        if delay > 0.0:
            time.sleep(delay)
        return self.read_values(format)

    def trigger(self):
        """Sends a software trigger to the device.
        """

        self.set_visa_attribute(VI_ATTR_TRIG_ID, VI_TRIG_SW)
        self.visalib.assert_trigger(self.session, VI_TRIG_PROT_DEFAULT)

    @property
    def term_chars(self):
        """Set or read a new termination character sequence (property).

        Normally, you just give the new termination sequence, which is appended
        to each write operation (unless it's already there), and expected as
        the ending mark during each read operation.  A typical example is CR+LF
        or just CR.  If you assign "" to this property, the termination
        sequence is deleted.

        The default is None, which means that CR is appended to each write
        operation but not expected after each read operation (but stripped if
        present).
        """

        return self.__term_chars

    @term_chars.setter
    def term_chars(self, term_chars):

        # First, reset termination characters, in case something bad happens.
        self.__term_chars = ""
        self.set_visa_attribute(VI_ATTR_TERMCHAR_EN, VI_FALSE)
        if term_chars == "" or term_chars is None:
            self.__term_chars = term_chars
            return
            # Only the last character in term_chars is the real low-level

        # termination character, the rest is just used for verification after
        # each read operation.
        last_char = term_chars[-1:]
        # Consequently, it's illogical to have the real termination character
        # twice in the sequence (otherwise reading would stop prematurely).

        if term_chars[:-1].find(last_char) != -1:
            raise ValueError("ambiguous ending in termination characters")

        self.set_visa_attribute(VI_ATTR_TERMCHAR, ord(last_char))
        self.set_visa_attribute(VI_ATTR_TERMCHAR_EN, VI_TRUE)
        self.__term_chars = term_chars

    @term_chars.deleter
    def term_chars(self):
        self.term_chars = None

    @property
    def send_end(self):
        """Whether or not to assert EOI (or something equivalent after each
        write operation.
        """

        return self.get_visa_attribute(VI_ATTR_SEND_END_EN) == VI_TRUE

    @send_end.setter
    def send_end(self, send):
        self.set_visa_attribute(VI_ATTR_SEND_END_EN, VI_TRUE if send else VI_FALSE)

    def wait_for_srq(self, timeout=25):
        """Wait for a serial request (SRQ) coming from the instrument.

        Note that this method is not ended when *another* instrument signals an
        SRQ, only *this* instrument.

        :param timeout: the maximum waiting time in seconds.
                        Defaul: 25 (seconds).
                        None means waiting forever if necessary.
        """
        lib = self.visalib

        lib.enable_event(self.session, VI_EVENT_SERVICE_REQ, VI_QUEUE)

        if timeout and not(0 <= timeout <= 4294967):
            raise ValueError("timeout value is invalid")

        starting_time = time.clock()

        while True:
            if timeout is None:
                adjusted_timeout = VI_TMO_INFINITE
            else:
                adjusted_timeout = int((starting_time + timeout - time.clock()) * 1000)
                if adjusted_timeout < 0:
                    adjusted_timeout = 0

            event_type, context = lib.wait_on_event(self.session, VI_EVENT_SERVICE_REQ,
                                                    adjusted_timeout)
            lib.close(context)
            if self.stb & 0x40:
                break

        lib.discard_events(self.session, VI_EVENT_SERVICE_REQ, VI_QUEUE)

    @property
    def stb(self):
        """Service request status register."""

        return self.visalib.read_stb(self.session)




