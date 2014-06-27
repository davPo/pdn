import skrf as rf
from pylab import *
import os

data_folder='results'
touchstone_file_lf = os.path.join(data_folder,'t520_10u_lfF.s1p')
touchstone_file = os.path.join(data_folder,'t520_10uF.s1p')
baseline= os.path.join(data_folder,'T520B476M010ATE035.s2p')

# Network 1
zmeas_lf = rf.Network(touchstone_file_lf)
zmeas=rf.Network(touchstone_file)

full_ntwk=rf.stitch(zmeas_lf[2:], zmeas)
full_ntwk.name='T520B_47uF10V_meas'

# Network 2
model_ntwk=rf.Network(baseline)
model_ntwk.name="T520B_47uF10V_model"

# Saving Network 1
full_ntwk.write_touchstone('T520B_47uF10V_meas.s1p','./results/',False,True)

# Plotting
rf.stylely() # matplotlib custom style from skrf.mplstyle
figure(figsize=(8,6))
loglog()

model_ntwk.plot_z_mag(m=0,n=0,marker='x', markevery=1, label='model')
full_ntwk.plot_z_mag(marker='+', markevery=1,label='measured')
title('Kemet T520B 47uF 10V' )
ylim([1e-2,1e2])
xlim([1e2,1e9])
# Save plot
rf.save_all_figs(dir='./results/', format=['png'],echo=True)
show()


