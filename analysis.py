import skrf as rf
from pylab import *

touchstone_file_lf = 't520_10u_lfF.s1p'
touchstone_file= 't520_10uF.s1p'
zmeas_lf = rf.Network(touchstone_file_lf)
zmeas=rf.Network(touchstone_file)


rf.stylely() # matplotlib custom style from skrf.mplstyle
figure(figsize=(8,4))
subplot(221)
s11.plot_s_db()
title('Z11 Magnitude')
subplot(222)
s11.plot_s_deg()
title('Z11 Phase')
tight_layout()
subplot(223)
title('Z mag')
loglog()
s11.plot_z_mag(marker='x', markevery=1)

show()