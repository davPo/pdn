import prologix

plx = prologix.prologix_ethernet('137.138.62.172')
hp4195 = plx.instrument(17)
print hp4195.ask('ID?')