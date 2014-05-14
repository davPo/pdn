
import numpy as npy
from visa import GpibInstrument
import visa

import prologix


hp4195 = plx.instrument(17)
print hp4195.ask('ID?')
from warnings import warn

from skrf.frequency import *
from skrf.network import *
from skrf import mathFunctions as mf

class HP4195(GpibInstrument):
    '''
    HP4195A
    '''
    def __init__(self, address=17,**kwargs):
        plx = prologix.prologix_ethernet('137.138.62.172')
        GpibInstrument.__init__(self,'GPIB::'+str(address),values_format = visa.single|visa.big_endian,**kwargs)
        self.timeout = 30
        self.echo=False

    def write(self, msg, *args, **kwargs):
        '''
        Write a msg to the instrument.
        Overload pyvisa method
        '''
        if self.echo:
            print msg
        return GpibInstrument.write(self,msg, *args, **kwargs)

    write.__doc__ = GpibInstrument.write.__doc__

    ## BASIC GPIB
    @property
    def idn(self):
        '''
        Identifying string for the instrument
        '''
        return self.ask('ID?')

    @property
    def status(self):
        '''
        Ask for indication that operations complete
        '''
        return self.ask('STB?')

    def reset(self):
        '''
        reset
        '''
        self.write('RST;')

    @property
    def error(self):
        return self.ask('ERR?')

    ## TRIGGER

    def set_trigger_continuous(self):
        '''
        Puts instrument on continuous trigger.

        Input:
            None

        Output:
            None
        '''
        self.write('SWM1')

    def set_trigger_single(self):
        '''
        Puts instrument on single. It will wait for
        trigger to initiate a trace.

        Input:
            None

        Output:
            None
        '''
        self.write('SWM2')

    def set_trigger_manual(self):
        '''
        Puts instrument on manual trigger .

        Input:
            None

        Output:
            None
        '''
        self.write('SWM3')

    def send_trigger(self):
        '''
        Send trigger to the instrument.

        Input:
            None

        Output:
            None
        '''
        self.write('SWTRG')

    def trigger_and_wait_till_done(self):
        '''
        send a manual trigger signal, and dont return untill operation
        is completed
        '''
        self.send_trigger()
        #status=self.status()
        self.wait_for_srq()
        #TODO check if it works

    @property
    def continuous(self):
        raise NotImplementedError

    @continuous.setter
    def continuous(self, choice):
        if choice:
            self.set_trigger_continuous()
        elif not choice:
            self.set_trigger_single()
        else:
            raise(ValueError('takes a boolean'))

    @property
    def averaging(self):
        '''
        averaging factor
        '''
        raise NotImplementedError

    @averaging.setter
    def averaging(self, factor ):
        raise NotImplementedError
        #self.write('AVERON %i;'%factor )

    @property
    def frequency(self, unit='hz'):
        freq=Frequency( float(self.ask('FMT1;START?')),\
                float(self.ask('FMT1;STOP?')),\
                int(float(self.ask('FMT1;NOP?'))),\
                'hz')
        freq.unit = unit
        return freq

    def read_register(self,register='A'):
        '''
        Read a data register using binary single format from the instrument.

        Input:
            register(string) to read

        Output:
            data (32 bits float)  : list of data points
        '''
        command="FMT3;%s?" %(register)
        data = self.ask_for_values(command)
        return data


    def set_measurement_network(self):
        '''
        Set network measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC1')


    def set_measurement_spectrum(self):
        '''
        Set spectrum measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC2')

    def set_measurement_impedance(self):
        '''
        Set impedance measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC3')

    def set_measurement_S11(self):
        '''
        Set S11 measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC4')

    def set_measurement_S22(self):
        '''
        Set S22 measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC7')

    def set_measurement_S12(self):
        '''
        Set S12 measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC6')

    def set_measurement_S21(self):
        '''
        Set S21 measurement.

        Input:
            None

        Output:
            None
        '''
        self.write('FNC5')

    def set_lin_freq(self):
        '''
        Set the frequency to linear scale.

        Input:
            None

        Output:
            None
        '''
        self.write('SWT1')

    def set_log_freq(self):
        '''
        Set the frequency to log scale.

        Input:
            None

        Output:
            None
        '''
        self.write('SWT2')
    ### parameters

    @property
    def sweep_time(self):
        '''
        Get sweep time from device
        '''
        return float(self.ask('FMT1;ST?'))

    @property
    def resbw(self):
        '''
        Get Resolution Bandwith.

        Input:
            None

        Output:
            bandwidth (float)   : Resolution bandwidth
        '''
        return self.ask('FMT1;RBW?')

    @resbw.setter
    def resbw(self, bw):
        '''
        Set Resolution Bandwidth.
        Can be 3, 10, 30, 100, 300, 1k, 3k, 10k, 30k, 100k, 300k

        Input:
            bw (float)

        Output:
            None
        '''
        self.write('RBW=%f' %bw)


    @property
    def numpoints(self):
        '''
        Get number of points in trace

        Input:
            None

        Output:
            numpoints (int) : Number of points in trace
        '''
        return self.ask('FMT1;NOP?')

    @numpoints.setter
    def numpoints(self, numpts):
        '''
        Set number of points in trace.
        Can be any number between 2-401.

        Input:
            numpts (int)    : number of points in trace

        Output:
            None
        '''
        self.write('NOP=%f' %numpts)


    @property
    def start_freq(self):
        '''
        Get start frequency.

        Input:
            None

        Output:
            freq (float)    : Start frequency
        '''
        #return float(self.ask('FMT1;START?'))
        return self.ask('FMT1;START?')

    @start_freq.setter
    def start_freq(self, freq):
        '''
        Set start frequency.

        Input:
            freq (float)    : Start frequency

        Output:
            None
        '''
        self.write('START=%f' %freq)

    @property
    def stop_freq(self):
        '''
        Get stop frequency.

        Input:
            None

        Output:
            freq (float)    : Stop frequency
        '''
        return (self.ask('FMT1;STOP?'))

    @stop_freq.setter
    def stop_freq(self, freq):
        '''
        Set stop frequency.

        Input:
            freq (float)    : Stop frequency

        Output:
            None
        '''
        self.write('STOP=%f' %freq)

    @property
    def center_freq(self):
        '''
        Get center frequency

        Input:
            None

        Output:
            freq (float) : Center Frequency
        '''
        return float(self.ask('FMT1;CENTER?'))

    @center_freq.setter
    def center_freq(self, freq):
        '''
        Set center frequency.

        Input:
            freq (float) : Center frequency

        Output:
            None
        '''
        self.write('CENTER=%f' %freq)


    @property
    def span_freq(self):
        '''
        Get span frequency.

        Input:
            None

        Output:
            freq (float) : Span frequency
        '''
        return float(self.ask('FMT1;SPAN?'))

    @span_freq.setter
    def span_freq(self, freq):
        '''
        Set span frequency.

        Input:
            freq (float) : Span frequency

        Output:
            None
        '''
        self.write('SPAN=%f' %freq)

    @property
    def power(self):
        '''
        Get power

        Input:
            None

        Output:
            pow (float) : Power
        '''
        return float(self.ask('FMT1;OSC1?'))


    @power.setter
    def power(self, pow):
        '''
        Set power.

        Input:
            pow (float) : Power

        Output:
            None
        '''
        self.write('OSC1=%f' % pow)

    @property
    def att_r1(self):
        '''
        Get attenuation port r1

        Input:
            None

        Output:
            att (dB): port r1 attenuation
        '''
        return int(float(self.ask('FMT1;ATR1?')))

    @att_r1.setter
    def att_r1(self,att):
        '''
        Set attenuator in port r1
        Can be 0,10,20,30,40,50.

        Input:
            att (dB) : port r1 attenuator
        
        Output:
            None
        '''
        self.write('ATR1=%f' %att)

    @property
    def att_t1(self):
        '''
        Get attenuation port t1

        Input:
            None

        Output:
            att (dB): port t1 attenuation
        '''
        return int(float(self.ask('FMT1;ATT1?')))

    @att_t1.setter
    def att_t1(self,att):
        '''
        Set attenuator in port t1
        Can be 0,10,20,30,40,50.

        Input:
            att (dB) : port t1 attenuator
        
        Output:
            None
        '''
        self.write('ATT1=%f' %att)

    
    @property
    def one_port(self):
        '''
        Initiates a sweep and returns a  Network type represting the
        data.
        '''
        self.continuous = False
        self.send_trigger()
        db_data = npy.array(self.read_register('A')) #MAG
        deg_data = npy.array(self.read_register('B')) #Phase

        data=npy.vstack((db_data,deg_data))
        data.shape=(-1,2)                                                                                        #ordering the data hopefully for integration into a skrf network
        #print data
        #print data.shape
        blah_spar=data[:,0]+1j*data[:,1]                                                                   #stolen from the skrf vna lib
        blah_spar.shape=(-1,1,1)
        ntwk = Network()
        ntwk.s = blah_spar
        #ntwk.s_db=db_data
        #ntwk.s_deg=deg_data
        ntwk.frequency= self.frequency
        self.continuous  = True
        return ntwk

    @property
    def two_port(self):
        '''
        Initiates a sweep and returns a  Network type represting the
        data.

        if you are taking multiple sweeps, and want the sweep timing to
        work, put the turn continuous mode off. like pnax.continuous='off'
        '''
        print ('s11')
        s11 = self.s11.s[:,0,0]
        print ('s12')
        s12 = self.s12.s[:,0,0]
        print ('s22')
        s22 = self.s22.s[:,0,0]
        print ('s21')
        s21 = self.s21.s[:,0,0]

        ntwk = Network()
        ntwk.s = npy.array(\
                [[s11,s21],\
                [ s12, s22]]\
                ).transpose().reshape(-1,2,2)
        ntwk.frequency= self.frequency

        return ntwk
    ##properties for the super lazy
    @property
    def s11(self):
        self.set_measurement_S11()
        ntwk =  self.one_port
        ntwk.name = 'S11'
        return ntwk
    @property
    def s22(self):
        self.set_measurement_S22()
        ntwk =  self.one_port
        ntwk.name = 'S22'
        return ntwk
    @property
    def s12(self):
        self.set_measurement_S12()
        ntwk =  self.one_port
        ntwk.name = 'S12'
        return ntwk
    @property
    def s21(self):
        self.set_measurement_S21()
        ntwk =  self.one_port
        ntwk.name = 'S21'
        return ntwk

    # @property
    # def switch_terms(self):
    #     '''
    #     measures forward and reverse switch terms and returns them as a
    #     pair of one-port networks.
    #
    #     returns:
    #             forward, reverse: a tuple of one ports holding forward and
    #                     reverse switch terms.
    #
    #     see also:
    #             skrf.calibrationAlgorithms.unterminate_switch_terms
    #
    #     notes:
    #             thanks to dylan williams for making me aware of this, and
    #             providing the gpib commands in his statistical help
    #
    #     '''
    #     print('forward')
    #     self.write('USER2;DRIVPORT1;LOCKA1;NUMEB2;DENOA2;CONV1S;')
    #     forward = self.one_port
    #     forward.name = 'forward switch term'
    #
    #     print ('reverse')
    #     self.write('USER1;DRIVPORT2;LOCKA2;NUMEB1;DENOA1;CONV1S;')
    #     reverse = self.one_port
    #     reverse.name = 'reverse switch term'
    #
    #     return (forward,reverse)


