import prologix

plx = prologix.PrologixEthernet('137.138.62.172')
hp4195 = plx.instrument(17)
print hp4195.ask('ID?')

a=hp4195.ask('A?')
print a.encode('hex')