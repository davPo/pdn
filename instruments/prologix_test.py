from prologix import *
import time

plx = PrologixEthernet('137.138.62.172')
print plx.version()
hp4195 = plx.instrument(17,values_format = single|big_endian)
hp4195.delay=0.2
hp4195.auto=0

#print hp4195.ask('ID?')

a=hp4195.ask_for_values('FMT3;A?')
b=hp4195.ask_for_values('FMT3;B?')
print a
print b