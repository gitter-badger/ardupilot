#!/usr/bin/env python

'''Test to see if we can communicate with FlightGear. This can
be done either using sockets (like in MavLink) or over 
telnet. Telnet may be better since it gives us the ability to specify
parameters to set and read, which makes for more readable code 
and the ability to do wind. 
Info on Telnet: http://forum.flightgear.org/viewtopic.php?f=36&t=16291
http://wiki.flightgear.org/Telnet_usage
However, Telnet is low bandwidth... 
Info on Generic protocol: http://wiki.flightgear.org/Generic_protocol
UDP connection: https://wiki.python.org/moin/UdpCommunication
'''
import sys, os, pexpect, socket
import math, time, select, struct, signal, errno

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'pysim'))

import util, atexit, fdpexpect
from pymavlink import fgFDM

#create and address out of a "<ip>:<port>" string
def interpret_address(addrstr):
	'''interpret a IP:port string'''
	a = addrstr.split(':')
	a[1] = int(a[1])
	return tuple(a)

class FGConnection(object):
	def __init__(self, fg_in_address, fg_out_address):
		self.fg_in_address = fg_in_address
		self.fg_out_address = fg_out_address
		#Startup socket for incomming messages from FG
		self.fg_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.fg_in.bind(fg_in_address)
		self.fg_in.setblocking(0)
		#Startup socket for outgoing messages to FG
		self.fg_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.fg_out.connect(fg_out_address)
		self.fg_out.setblocking(0)
		self.fdm = fgFDM.fgFDM()


	def sendPacket(self, pkt):
		return 0

	#parses the fdm packet from flightgear if there is one
	def readPacket(self):
		if self.fg_in.fileno() :
			buf = self.fg_in.recv(self.fdm.packet_size())
			self.fdm.parse(buf)

	def printPacket(self):
		print("asl=%.1f agl=%.1f roll=%.1f pitch=%.1f a=(%.2f %.2f %.2f)" % (
			self.fdm.get('altitude', units='meters'),
			self.fdm.get('agl', units='meters'),
			self.fdm.get('phi', units='degrees'),
			self.fdm.get('theta', units='degrees'),
			self.fdm.get('A_X_pilot', units='mpss'),
			self.fdm.get('A_Y_pilot', units='mpss'),
			self.fdm.get('A_Z_pilot', units='mpss')))
				

'''Read the UDP socket from FlightGear'''

'''Write to the UDP socket for FlightGear'''

'''Sets some parameter p to value v in FlightGear'''

'''Reads some parameter p from FlightGear'''

'''Once we can communicate with FlightGear, then check to see if we 
can communicate with the SITL. This is going to be hard, need to read over 
runsim.py and figure out how the connection to the SITL works'''


class SITLConnection(object):
	def __init__(self, in_address, out_address):
		self.in_address = in_address
		self.out_address = out_address

		#intput from SITL
		self.sim_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sim_in.bind(in_address)
		self.sim_in.setblocking(0)

		#output from the SITL
		self.sim_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sim_out.connect(out_address)
		self.sim_out.setblocking(0)

		#storage for control surfaces
		self.aileron = 0
		self.elevator = 0
		self.throttle = 0
		self.rudder = 0

	#opts is the parsed options
	def readPacket(self, opts):
		'''process control changes from SITL sim'''
		#the packet size for the sim input in 28 bytes
		simbuf = sim_in.recv(28)
		process_sitl_input(simbuf)
		control = list(struct.unpack('<14H', buf))
		pwm = control[:11]
		(speed, direction, turbulance) = control[11:]

		#not quite sure why this is coming from th SITL....
		global wind
		wind.speed      = speed*0.01
		wind.direction  = direction*0.01
		wind.turbulance = turbulance*0.01

		self.aileron  = (pwm[0]-1500)/500.0
		self.elevator = (pwm[1]-1500)/500.0
		self.throttle = (pwm[2]-1000)/1000.0
		if opts.revthr:
			self.throttle = 1.0 - throttle
			self.rudder   = (pwm[3]-1500)/500.0

		

	#state is of type fgFDM
	def sendSITL(state):
		simbuf = struct.pack('<17dI',
			state.get('latitude', units='degrees'),
			state.get('longitude', units='degrees'),
			state.get('altitude', units='meters'),
			state.get('psi', units='degrees'),
			state.get('v_north', units='mps'),
			state.get('v_east', units='mps'),
			state.get('v_down', units='mps'),
			state.get('A_X_pilot', units='mpss'),
			state.get('A_Y_pilot', units='mpss'),
			state.get('A_Z_pilot', units='mpss'),
			state.get('phidot', units='dps'),
			state.get('thetadot', units='dps'),
			state.get('psidot', units='dps'),
			state.get('phi', units='degrees'),
			state.get('theta', units='degrees'),
			state.get('psi', units='degrees'),
			state.get('vcas', units='mps'),
			0x4c56414f) 
		#TODO: Acutally send the information 



##################
# main program
from optparse import OptionParser
parser = OptionParser("runsim.py [options]")
parser.add_option("--simin",   help="SITL input (IP:port)",          default="127.0.0.1:5502")
parser.add_option("--simout",  help="SITL output (IP:port)",         default="127.0.0.1:5501")
parser.add_option("--fgout",   help="Output to FG (IP:port)",   default="127.0.0.1:5503")
parser.add_option("--fgin",   help="Input from FG (IP:port)",   default="127.0.0.1:5504")
parser.add_option("--home",    type='string', help="home lat,lng,alt,hdg (required)")
parser.add_option("--script",  type='string', help='jsbsim model script', default='jsbsim/easystar_test.xml')
parser.add_option("--options", type='string', help='jsbsim startup options')
parser.add_option("--elevon", action='store_true', default=False, help='assume elevon input')
parser.add_option("--revthr", action='store_true', default=False, help='reverse throttle')
parser.add_option("--vtail", action='store_true', default=False, help='assume vtail input')
parser.add_option("--wind", dest="wind", help="Simulate wind (speed,direction,turbulance)", default='0,0,0')

(opts, args) = parser.parse_args()

os.chdir(util.reltopdir('Tools/autotest'))


APM = SITLConnection(interpret_address(opts.simin), interpret_address(opts.simout))
FG = FGConnection(interpret_address(opts.fgin), interpret_address(opts.fgout))


def mainLoop():
	while True:
		rin = [FG.fg_in.fileno(), APM.sim_in.fileno()]
		rout = [FG.fg_out.fileno(), APM.sim_out.fileno()]
		try:
			(rin, win, xin) = select.select(rin, rout, [], 0)
		except select.error:
			print("error")
			continue
		if FG.fg_in.fileno() in rin:
			FG.readPacket()
			FG.printPacket()

		if APM.sim_in.fileno() in rin:
			APM.readPacket(opts)


mainLoop()


