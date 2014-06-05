import skrf as rf
from pylab import *
from instruments import HP4195

myvna=HP4195()
#myvna.reset()
s11=myvna.s11
s11.comments='VddCM'
s11.name="Z11"


# s11.comments='VddCM'
# s11.name="Z11"
# figure()
# s11.plot_s_db(label= 'Mag(db)')
# s11.plot_s_deg(label= 'Phase(deg)')
# show()

# Saving to file
# --------------
s11.write_touchstone('test','./results/',False,True)
# Plotting
# --------
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
s11.plot_z_mag()
show()