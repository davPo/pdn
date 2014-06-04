import skrf as rf
from pylab import *
from instruments import HP4195


myvna=HP4195()
#myvna.reset()
s11=myvna.s11
#print s11
#print s11.s_db
#print s11.s_deg

rf.stylely()

s11.plot_s_db()
s11.plot_s_deg()
show()

#print myvna.s22



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