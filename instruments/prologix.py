"""


"""

from serial import Serial
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP
from time import sleep,clock

import warnings
import errors
from util import (split_kwargs, warn_for_invalid_kwargs,parse_ascii, parse_binary)

# From pyVisa

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

#
class _prologix_base(object):
    """
    Base class for Prologix controllers (ethernet/usb)

    """

    def __init__(self):
        """
        initialization routines common to USB and ethernet

        """
        # keep a local copy of the current address
        # and read-after write setting
        # so we're not always asking for it
        self._addr = self.addr
        self._auto = self.auto

        self._timeout=5 #default timeout value

    @property
    def timeout(self):
        """The timeout in seconds for all resource I/O operations.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if not(1 <= value <= 30):
            raise ValueError("timeout value is invalid")
        self._timeout=int(value)

    # use addr to select an instrument by its GPIB address

    @property
    def addr(self):
        """
        The Prologix controller can calk to one instrument
        at a time. This sets the GPIB address of the
        currently addressed instrument.

        Use this attribute to set or check which instrument
        is currently selected:

        >>> plx.addr
        9
        >>> plx.addr = 12
        >>> plx.addr
        12

        """
        # query the controller for the current address
        # and save it in the _addr variable (why not)
        self._addr = int(self.ask("++addr"))
        return self._addr
    @addr.setter
    def addr(self, new_addr):
        # update local record
        self._addr = new_addr
        # change to the new address
        self.write("++addr %d" % new_addr)
        # we update the local variable first because the 'write'
        # command may have a built-in lag. if we intterupt a program
        # during this period, the local attribute will be wrong

    @property
    def auto(self):
        """
        Boolean. Read-after-write setting.

        The Prologix 'read-after-write' setting can
        automatically address instruments to talk after
        writing to them. This is usually convenient, but
        some instruments do poorly with it.

        """
        self._auto = bool(int(self.ask("++auto")))
        return self._auto
    @auto.setter
    def auto(self, val):
        self._auto = bool(val)
        self.write("++auto %d" % self._auto)

    def version(self):
        """ Check the Prologix firmware version. """
        return self.ask("++ver")

    @property
    def savecfg(self):
        """
        Boolean. Determines whether the controller should save its
        settings in EEPROM.

        It is usually best to turn this off, since it will
        reduce `wear on the EEPROM`_ in applications that
        involve talking to more than one instrument.

        .. _`wear on the EEPROM`: http://www.febo.com/pipermail/time-nuts/2009-July/038952.html

        """
        resp = self.ask("++savecfg")
        if resp == 'Unrecognized command':
            raise Exception("""
                Prologix controller does not support ++savecfg
                update firmware or risk wearing out EEPROM
                            """)
        return bool(int(resp))
    @savecfg.setter
    def savecfg(self, val):
        d = bool(val)
        self.write("++savecfg %d" % d)

    def instrument(self, addr, **kwargs):
        """
        Factory function for :class:`instrument` objects.

        >>> plx.instrument(12)

        is equivalent to

        >>> instrument(plx, 12)

        `addr` -- the GPIB address for an instrument
                  attached to this controller.
        """
        return Instrument(self, addr, **kwargs)

class PrologixEthernet(_prologix_base):
    """
    Interface to a Prologix GPIB-Ethernet controller.

    To instantiate, use the ``prologix_ethernet`` factory:

    >>> plx = prologix.prologix_ethernet('128.223.xxx.xxx')

    Replace the ``xxx``es with the controller's actual ip
    address, found using the Prologix Netfinder tool.


    """

    def __init__(self, ip):
        # open a socket to the controller
        self.bus = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        self.bus.settimeout(2)
        self.bus.connect((ip, 1234))

        # change to controller mode
        self.bus.send('++mode 1\n')

        # do common startup routines
        super(PrologixEthernet, self).__init__()

    def write(self, command, lag=0.1):
        self.bus.send("%s\n" % command)
        sleep(lag)

    def readall(self,chunk_size=100):
        resp = self.bus.recv(chunk_size) #100 should be enough, right?
        return resp.rstrip()

    def ask(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        # no need to clear buffer
        self.write(query, *args, **kwargs)
        return self.readall()


class PrologixUSB(_prologix_base):
    """
    Interface to a Prologix GPIB-USB controller.

    To instantiate, specify the virtual serial port where the
    controller is plugged in:

    >>> plx = prologix.prologix_USB('/dev/ttyUSBgpib')

    On Windows, you could use something like

    >>> plx = prologix.prologix_USB('COM1')

    """

    def __init__(self, port='/dev/ttyUSBgpib', log=False):
        # create a serial port object
        self.bus = Serial(port, baudrate=115200, rtscts=1, log=log)
        # if this doesn't work, try settin rtscts=0

        # flush whatever is hanging out in the buffer
        self.bus.readall()

        # don't save settings (to avoid wearing out EEPROM)
        self.savecfg = False

        # do common startup routines
        super(PrologixUSB, self).__init__()

    def write(self, command, lag=0.1):
        self.bus.write("%s\r" % command)
        sleep(lag)

    def readall(self):
        resp = self.bus.readall()
        return resp.rstrip()

    def ask(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        #TODO: if bus doesn't have a logger
        self.bus.logger.debug('clearing buffer - expect no result')
        self.readall()  # clear the buffer
        self.write(query, *args, **kwargs)
        return self.readall()

controllers = dict()

def prologix_ethernet(ip):
    """
    Factory function for a Prologix GPIB-Ethernet controller.

    To instantiate, specify the IP address of the controller:

    >>> plx = prologix.prologix_ethernet('128.223.xxx.xxx')

    """
    if ip not in controllers:
        controllers[ip] = PrologixEthernet(ip)
    return controllers[ip]

def prologix_USB(port='/dev/ttyUSBgpib', log=False):
    """
    Factory for a Prologix GPIB-USB controller.

    To instantiate, specify the virtual serial port where the
    controller is plugged in:

    >>> plx = prologix.prologix_USB('/dev/ttyUSBgpib')

    On Windows, you could use something like

    >>> plx = prologix.prologix_USB('COM1')

    """
    if port not in controllers:
        controllers[port] = PrologixUSB(port)
    return controllers[port]

class Instrument(object):
    """
    Represents an instrument attached to
    a Prologix controller.

    Pass the controller instance and GPIB address
    to the constructor. This creates a GPIB instrument
    at address 12:

    >>> plx = prologix_USB()
    >>> inst = instrument(plx, 12)

    A somewhat nicer way to do the second step would be to use the
    :meth:`instrument` factory method of the Prologix controller:

    >>> inst = plx.instrument(12)

    Once we have our instrument object ``inst``, we can use the
    :meth:`ask` and :meth:`write` methods to send GPIB queries and
    commands.

    """

    delay = 0.1
    """Seconds to pause after each write."""
    #From PyVISA
    """
    :param timeout: the VISA timeout for each low-level operation in
                    milliseconds.
    :param term_chars: the termination characters for this device.
    :param chunk_size: size of data packets in bytes that are read from the
                       device.
    :param ask_delay: waiting time in seconds after each write command.
                      Default: 0.1
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
                      'ask_delay': 0.1,
                      'send_end': True,
                      #: floating point data value format
                      'values_format': ascii,
                        # header for binary format
                      'header': b"#A"
                        }

    def __init__(self, controller, addr,**kwargs):
        """
        Constructor method for instrument objects.

        required arguments:
            controller -- the prologix controller instance
                to which this instrument is attached.
            addr -- the address of the instrument
                on controller's GPIB bus.

        keyword arguments:
            delay -- seconds to wait after each write.
            auto -- read-after-write setting.

        """
        self.addr = addr
        self.auto = False
        #self.delay = 0.1 # now in kwargs
        self.controller = controller

        for key, value in Instrument.DEFAULT_KWARGS.items():
            setattr(self, key, kwargs.get(key, value))

    def _get_priority(self):
        """
        configure the controller to address this instrument

        """
        # configure instrument-specific settings
        if self.auto != self.controller._auto:
            self.controller.auto = self.auto
        # switch the controller address to the
        # address of this instrument
        if self.addr != self.controller._addr:
            self.controller.addr = self.addr

#     def ask(self, command):
#         """
#         Send a query the instrument, then read its response.
#
#         Equivalent to :meth:`write` then :meth:`read`.
#
#         For example, get the 'ID' string from an EG&G model
#         5110 lock-in:
#
#         >>> inst.ask('ID')
#         '5110'
#
#         Is the same as:
#
#         >>> inst.write('ID?')
#         >>> inst.read()
#         '5110'
#
#         """
#         # clear stray bytes from the buffer.
#         # hopefully, there will be none.
#         # if there are, print a warning
# #        clrd = self.controller.bus.inWaiting()
# #        if clrd > 0:
# #            print clrd, 'bytes cleared'
# #        self.read()  # clear the buffer
#         self.write(command)
#         return self.read()

    def read(self): # behaves like readall
        """
        Read a response from an instrument.

        """
        self._get_priority()
        if not self.auto:
            # explicitly tell instrument to talk.
            self.controller.write('++read eoi',self.ask_delay)
        return self.controller.readall()

    def write(self, command):
        """
        Write a command to the instrument.

        """
        self._get_priority()
        self.controller.write(command, lag=self.ask_delay)


    # From Pyvisa

    #FIXME:To correct
    def write_raw(self, message):
        """Write a string message to the device.

        The term_chars are appended to it, unless they are already.

        :param message: the message to be sent.
        :type message: bytes
        :return: number of bytes written.
        :rtype: int
        """

        self._get_priority()
        self.controller.write(message, lag=self.ask_delay)

        return 0

    #FIXME:already defined
    # def write(self, message):
    #     """Write a string message to the device.
    #
    #     The term_chars are appended to it, unless they are already.
    #
    #     :param message: the message to be sent.
    #     :type message: unicode (Py2) or str (Py3)
    #     :return: number of bytes written.
    #     :rtype: int
    #     """
    #
    #     if self.__term_chars and not message.endswith(self.__term_chars):
    #         message += self.__term_chars
    #     elif self.__term_chars is None and not message.endswith(CR + LF):
    #         message += CR + LF
    #
    #     count = self.write_raw(message.encode('ascii'))
    #
    #     return count

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

    #FIXME:Modified to test
    def read_raw(self):
        """Read the unmodified string sent from the instrument to the computer.

        In contrast to read(), no termination characters are checked or
        stripped. You get the pristine message.

        :rtype: bytes

        """
        ret = bytes()
        self._get_priority()
        if not self.auto:
            # explicitly tell instrument to talk.
            self.controller.write('++read eoi', lag=self.ask_delay)
        ret+= self.controller.readall(self.chunk_size)
        return ret

    # def read(self):
    #     """Read a string from the device.
    #
    #     Reading stops when the device stops sending (e.g. by setting
    #     appropriate bus lines), or the termination characters sequence was
    #     detected.  Attention: Only the last character of the termination
    #     characters is really used to stop reading, however, the whole sequence
    #     is compared to the ending of the read string message.  If they don't
    #     match, a warning is issued.
    #
    #     All line-ending characters are stripped from the end of the string.
    #
    #     :rtype: str
    #     """
    #
    #     return self._strip_term_chars(self.read_raw().decode('ascii'))

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
            return parse_binary(data, fmt & 0x04 == big_endian, is_single,self.header)
        except ValueError as e:
            raise errors.InvalidBinaryFormat(e.args)

    def ask(self, message, delay=None):
        """A combination of write(message) and read()

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
            sleep(delay)
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
            sleep(delay)
        return self.read_values(format)

    def trigger(self):
        """Sends a software trigger to the device.
        """


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

        self.__term_chars = term_chars

    @term_chars.deleter
    def term_chars(self):
        self.term_chars = None

    @property
    def send_end(self):
        """Whether or not to assert EOI (or something equivalent after each
        write operation.
        """

        self.controller.write('++eoi')
        return self.controller.readall()

    @send_end.setter
    def send_end(self, send):
        if send is True:
            self.controller.write('++eoi 1')
        else:
            self.controller.write('++eoi 0')


    def wait_for_srq(self, timeout=25):
        """Wait for a serial request (SRQ) coming from the instrument.

        Note that this method is not ended when *another* instrument signals an
        SRQ, only *this* instrument.

        :param timeout: the maximum waiting time in seconds.
                        Defaul: 25 (seconds).
                        None means waiting forever if necessary.
        """

        if timeout and not(0 <= timeout <= 4294967):
            raise ValueError("timeout value is invalid")

        starting_time = clock()

        while True:
            if timeout is None:
                pass
                adjusted_timeout = 10 #VI_TMO_INFINITE
            else:
                adjusted_timeout = int((starting_time + timeout - clock()) * 1000)
                if adjusted_timeout < 0:
                    adjusted_timeout = 0

            #event_type, context = lib.wait_on_event(self.session, VI_EVENT_SERVICE_REQ,adjusted_timeout)
            #lib.close(context)
            if self.stb & 0x40:
                break

        #lib.discard_events(self.session, VI_EVENT_SERVICE_REQ, VI_QUEUE)

    @property
    def stb(self):
        """Service request status register."""
        return 1
        #return self.visalib.read_stb(self.session)
