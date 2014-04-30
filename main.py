#from HP4195A import HP4195A
import skrf as rf
from pylab import *
from instruments import HP4195


myvna=HP4195(address=17)
myvna.reset()


#import visa
#rm = visa.ResourceManager()
#print rm.list_resources()
#vna4195 = rm.get_instrument('GPIB0::17::INSTR',values_format=0x01+0x04)
#vna4195.write("GRT0")


#myvna= HP4195A(name='myvna',address='GPIB0::17::INSTR',reset=False)
#myvna.default_init()
#print myvna.get_start_freq()
#print myvna.get_stop_freq()
#traceA=myvna.get_trace('lin','A')
#traceB=myvna.get_trace('lin','B')
# tupple  (f,data) / f is array of frequency / data is array of data
#print traceA[1]
#print traceB[1]
#print traceA[0]



#data=traceA[1][1:100]+1j*(traceB[1][1:100])
#print data
#print traceA[0].shape
#impedance=rf.network.Network(name='Z_PDN',comments='4W_Z11')
#impedance.f, impedance.z,impedance.z0 = traceA[0][1:100],data,[50+0.j]
#impedance.z.
#impedance.f=traceA[0]
#impedance.z=traceA[1]
#impedance.s_deg=traceB[1]
#print impedance.z_mag
#impedance.plot_it_all()

#impedance.plot_z_mag()
#impedance.plot_s_deg()
#plot=rf.plotting.plot_rectangular(impedance.f,x_label='F',y_label='Ohms',title='PDN meas',show_legend=True, axis='tight', ax=None)
#show()