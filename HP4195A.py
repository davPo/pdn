import visa
import types
import logging
from time import sleep
import struct
import numpy

# from pyvisa
ascii      = 0
single     = 1
double     = 3
big_endian = 4

CR = '\r'
LF = '\n'
#


class HP4195A():
    '''
    This is the python driver for the HP 4195A
    network analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>', 'HP_4195A', address='<GPIB address>',
        reset=<bool>)

    The last parameter is optional. Default is reset=False

    TODO:
    1. make todo list
    2. ask Pieter about the purpose of the specific tools
    3. fix docstrings
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_4195A, and communicates with the wrapper

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false
        '''

        self._address = address
        self._visainstrument = visa.instrument(self._address,values_format = single|big_endian)

        self._visainstrument.timeout = 30
        # BEWARE! in case of low IFWB, it might be
        # necessary to add additional delay
        # ( ~ numpoints / IFBW ) yourself!

      #  self.get_all()

    def get_all(self):

        sl = 1

        print self.get_start_freq()
        sleep(sl)

        print self.get_stop_freq()
        sleep(sl)

#        self.get_center_freq()
#        sleep(s1)
#
#        self.get_span_freq()
#        sleep(sl)
#
        self.get_resbw()
        sleep(sl)

        self.get_numpoints()
        sleep(sl)

#        self.get_power()
        sleep(sl)

#        self.get_att_r1()
        sleep(sl)

 #       self.get_att_t1()
        sleep(sl)

  #      self.get_sweep_time()
        sleep(sl)

    def default_init(self):

        sl = 0.5

        print 'resetting'
        self.reset()
        sleep(sl)

#        print 'set format logm'
#        self.set_format_logm()
#        sleep(sl)
        print 'set measurement impedance'
        self.set_measurement_impedance()
        sleep(sl)
        print 'set source power -10dBm'
        self.set_power(-10.0)
        sleep(sl)
        print 'setting port attenuation'
        self.set_att_r1(10)
        sleep(sl)
        self.set_att_t1(10)
        sleep(sl)
        print 'set start freq 1k'
        self.set_start_freq(1e3)
        sleep(sl)
        print 'set stop freq 100M'
        self.set_stop_freq(10e6)
        sleep(sl)
        print 'set resolution bandwidth 1k'
        self.set_resbw(3000)
        sleep(sl)
        print 'set numpoints'
        self.set_numpoints(401)
        sleep(sl)

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('RST')

    def set_trigger_continuous(self):
        '''
        Puts instrument on continuous trigger. 

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SWM1')

    def set_trigger_single(self):
        '''
        Puts instrument on single. It will wait for 
        trigger to initiate a trace.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SWM2')

    def set_trigger_manual(self):
        '''
        Puts instrument on manual trigger .

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SWM3')


    def send_trigger(self):
        '''
        Send trigger to the instrument.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SWTRG')

    def read_register(self,register='A'):
        '''
        Read a data register using binary single format from the instrument.

        Input:
            register(string) to read

        Output:
            data (32 bits float)  : list of data points
        '''
        command="FMT3;%s?" %(register)
        data = self._visainstrument.ask_for_values(command)
        return data

#### Functions for doing measurements

    def get_trace(self, mode='lin', trace='B'):
        '''
        Send trigger to device, wait for aquiring the data,
        and read back the data from the device.
        '''
        #qt.mstart()

        startfreq = self.get_start_freq()
        stopfreq = self.get_stop_freq()
        numpoints = self.get_numpoints()

        if mode=='lin':
            freqs = numpy.linspace(float(startfreq), float(stopfreq),int(numpoints))
        elif mode=='log':
            freqs = numpy.logspace(numpy.log10(float(startfreq)),numpy.log10(float(stopfreq)),int(numpoints))
        else:
            print 'mode needs to be either "lin" or "log"!'
            return False

        sweep_time = self.get_sweep_time()
        
        print 'sending trigger to network analyzer, and wait to finish'
        print 'estimated waiting time: %.2f s' % sweep_time
        self.send_trigger()
        #qt.msleep(sweep_time)
    
        print 'readout network analyzer'
        reply = self.read_register(trace)
        reply = numpy.array(reply)
    
        return (freqs, reply)

    def save_trace(self, filepath=None, plot=True):
        '''
        runs 'get_trace()' and saves the output to a file.

        Input:
            filepath (string):  Path to where the file should be saved.(optional)

        Output:
            filepath (string):  The filepath where the file has been created.
        '''
        #TODO: change value label 'S_ij' to represent actual measurement
        freqs, reply = self.get_trace()
        #d = qt.Data(name='netan')
        #d.add_coordinate('freq [Hz]')
        #d.add_value('S_ij [dB]')
        #d.create_file(filepath=filepath)
        #d.add_data_point(zip(freqs, reply))
        #d.close_file()
       # if plot:
         #   p = qt.plot(d, name='netan', clear=True)
         #   p.save_png()
         #   p.save_gp()
       # return d.get_filepath()

    def plot_trace(self):
        '''
        performs a measurement and plots the data.
        '''
        freqs, reply = self.get_trace()
        #qt.plot(freqs, reply, name='netan',
        #        xlabel='freq [Hz]', ylabel='S_ij [dB]',
        #        clear=True)

####

    def set_measurement_network(self):
        '''
        Set network measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC1')


    def set_measurement_spectrum(self):
        '''
        Set spectrum measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC2')

    def set_measurement_impedance(self):
        '''
        Set impedance measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC3')

    def set_measurement_S11(self):
        '''
        Set S11 measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC4')

    def set_measurement_S22(self):
        '''
        Set S22 measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC7')

    def set_measurement_S12(self):
        '''
        Set S12 measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC6')

    def set_measurement_S21(self):
        '''
        Set S21 measurement.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FNC5')

    def set_lin_freq(self):
        '''
        Set the frequency to linear scale.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SWT1')

    def set_log_freq(self):
        '''
        Set the frequency to log scale.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SWT2')

#    def set_format_logm(self):
#        '''
#        Set output format display to 'log magnitude'.
#
#        Input:
#            None
#
#        Output:
#            None
#        '''
#        self._visainstrument.write('SCT2')
#    
#    def set_format_linm(self):
#        '''
#        Set output format display to 'linear magnitude'.
#
#        Input:
#            None
#
#        Output:
#            None
#        '''
#        self._visainstrument.write('SCT1')
#
#    def set_format_phas(self):
#        '''
#        Set output format to 'phase'.
#
#        Input:
#           None
#
#        Output:
#            None
#        '''
#        self._visainstrument.write('PHAS;')

    def set_port1(self):
        '''
        Set R1/T1 in NA
        Input:
            None
        Output:
            None
        '''
        self._visainstrument.write('PORT1')

    def set_port2(self):
        '''
        Set R1/T2 in NA
        Input:
            None
        Output:
            None
        '''
        self._visainstrument.write('PORT2')
    
    def set_port3(self):
        '''
        Set R1/R2 in NA
        Input:
            None
        Output:
            None
        '''
        self._visainstrument.write('PORT3')
    
    def set_port4(self):
        '''
        Set T1/R2 in NA
        Input:
            None
        Output:
            None
        '''
        self._visainstrument.write('PORT4')
    
    def set_port5(self):
         '''
         Set T2/R2 in NA
         Input:
             None
         Output:
             None
         '''
         self._visainstrument.write('PORT5')
     


### parameters

    def get_sweep_time(self):
        '''
        Get sweep time from device
        '''
        return float(self._visainstrument.ask('FMT1;ST?'))

    def set_resbw(self, bw):
        '''
        Set Resolution Bandwidth.
        Can be 3, 10, 30, 100, 300, 1k, 3k, 10k, 30k, 100k, 300k

        Input:
            bw (float)

        Output:
            None
        '''
        self._visainstrument.write('RBW=%f' %bw)


    def get_resbw(self):
        '''
        Get Resolution Bandwith.

        Input:
            None

        Output:
            bandwidth (float)   : Resolution bandwidth
        '''
        return self._visainstrument.ask('FMT1;RBW?')

    def set_numpoints(self, numpts):
        '''
        Set number of points in trace.
        Can be any number between 2-401.

        Input:
            numpts (int)    : number of points in trace

        Output:
            None
        '''
        self._visainstrument.write('NOP=%f' %numpts)
        #self.get_sweep_time()

    def get_numpoints(self):
        '''
        Get number of points in trace

        Input:
            None

        Output:
            numpoints (int) : Number of points in trace
        '''
        return self._visainstrument.ask('FMT1;NOP?')

    def set_start_freq(self, freq):
        '''
        Set start frequency.

        Input:
            freq (float)    : Start frequency

        Output:
            None
        '''
        self._visainstrument.write('START=%f' %freq)

    def get_start_freq(self):
        '''
        Get start frequency.

        Input:
            None

        Output:
            freq (float)    : Start frequency
        '''
        #return float(self._visainstrument.ask('FMT1;START?'))
        return self._visainstrument.ask('FMT1;START?')

    def set_stop_freq(self, freq):
        '''
        Set stop frequency.

        Input:
            freq (float)    : Stop frequency

        Output:
            None
        '''
        self._visainstrument.write('STOP=%f' %freq)

    def get_stop_freq(self):
        '''
        Get stop frequency.

        Input:
            None

        Output:
            freq (float)    : Stop frequency
        '''
        return (self._visainstrument.ask('FMT1;STOP?'))


    def set_center_freq(self, freq):
        '''
        Set center frequency.

        Input:
            freq (float) : Center frequency

        Output:
            None
        '''
        self._visainstrument.write('CENTER=%f' %freq)

    def get_center_freq(self):
        '''
        Get center frequency

        Input:
            None

        Output:
            freq (float) : Center Frequency
        '''
        return float(self._visainstrument.ask('FMT1;CENTER?'))

    def set_span_freq(self, freq):
        '''
        Set span frequency.

        Input:
            freq (float) : Span frequency

        Output:
            None
        '''
        self._visainstrument.write('SPAN=%f' %freq)

    def get_span_freq(self):
        '''
        Get span frequency.

        Input:
            None

        Output:
            freq (float) : Span frequency 
        '''
        return float(self._visainstrument.ask('FMT1;SPAN?'))

    def set_power(self, pow):
        '''
        Set power.

        Input:
            pow (float) : Power

        Output:
            None
        '''
        self._visainstrument.write('OSC1=%f' % pow)

    def get_power(self):
        '''
        Get power

        Input:
            None

        Output:
            pow (float) : Power
        '''
        return float(self._visainstrument.ask('FMT1;OSC1?'))

    def set_att_r1(self,att):
        '''
        Set attenuator in port r1
        Can be 0,10,20,30,40,50.

        Input:
            att (dB) : port r1 attenuator
        
        Output:
            None
        '''
        self._visainstrument.write('ATR1=%f' %att)

    def get_att_r1(self):
        '''
        Get attenuation port r1

        Input:
            None
        
        Output:
            att (dB): port r1 attenuation
        '''
        return int(float(self._visainstrument.ask('FMT1;ATR1?')))
    
    def set_att_t1(self,att):
        '''
        Set attenuator in port t1
        Can be 0,10,20,30,40,50.

        Input:
            att (dB) : port t1 attenuator
        
        Output:
            None
        '''
        self._visainstrument.write('ATT1=%f' %att)

    def get_att_t1(self):
        '''
        Get attenuation port t1

        Input:
            None
        
        Output:
            att (dB): port t1 attenuation
        '''
        return int(float(self._visainstrument.ask('FMT1;ATT1?')))



