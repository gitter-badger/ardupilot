
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

	#packet is of type servos
	def sendPacket(self, pkt):
		servoList = []
		#1 index because of the real world
		for ch in range(1,5):
			#servoList.append(pkt.scale_channel(ch, getattr(pkt, 'ch%u' % ch)))
			servoList.append(getattr(pkt, 'ch%u' % ch))
		buf = struct.pack('!4d', *servoList)
		try:
			self.fg_out.send(buf)
		except socket.error as e:
			raise

	#parses the fdm packet from flightgear if there is one
	def readPacket(self):
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
				
class control(object):
    def __init__(self,aileron,rudder,throttle,elevator):
        self.aileron = aileron;
        self.rudder = rudder;
        self.throttle = throttle;
        self.elevator = elevator;

    def controlPrint(self):
        print self.aileron;
        print self.rudder;
        print self.throttle;
        print self.elevator;

class servos(object):
    def __init__(self,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,ch9,ch10, ch11):
        self.ch1 = ch1
        self.ch2 = ch2
        self.ch3 = ch3
        self.ch4 = ch4
        self.ch5 = ch5
        self.ch6 = ch6
        self.ch7 = ch7
        self.ch8 = ch8
        self.ch9 = ch9
        self.ch10 = ch10
        self.ch11 = ch11

    def set_servos(self, servoL):
    	#ailerons
		self.ch1 = self.scale_channel(servoL[0])
		#elevator
		self.ch2 = self.scale_channel(servoL[1])
		#throttle
		self.ch3 = self.scale_channel(servoL[2], 1000)
		#rudder
		self.ch4 = self.scale_channel(servoL[3])
		self.ch5 = self.scale_channel(servoL[4])
		self.ch6 = self.scale_channel(servoL[5])
		self.ch7 = self.scale_channel(servoL[6])
		self.ch8 = self.scale_channel(servoL[7])
		self.ch9 = self.scale_channel(servoL[8])
		self.ch10 = self.scale_channel(servoL[9])
		self.ch11 = self.scale_channel(servoL[10])


    def scale_channel(self, value, midval=1500, divval=600.0):
	    '''scale a channel to 1000/1500/2000'''
	    v = (value-midval)/divval
	    if v < -1:
	        v = -1
	    elif v > 1:
	        v = 1
	    #used to add 1500 and *500, but this was scaled wrong -> just using v
	    return float(v)

    def servosPrint(self):
        print self.ch1,' ',self.ch2,' ',self.ch3,' ',self.ch4,' ',self.ch5,' ',self.ch6,' ',self.ch7,' ',self.ch8,' ',self.ch9,' ',self.ch10,' ',self.ch11

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

		#input from SITL
		self.sim_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sim_in.bind(in_address)
		self.sim_in.setblocking(0)

		#output to the SITL
		self.sim_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sim_out.connect(out_address)
		self.sim_out.setblocking(0)

		#storage for control surfaces
		self.aileron = 0
		self.elevator = 0
		self.throttle = 0
		self.rudder = 0
		self.controlServos = servos(0,0,0,0,0,0,0,0,0,0,0)

	def readPacket(self):
		'''process control changes from SITL sim, returns type control'''
		#the packet size for the sim input in 28 bytes
		simbuf = APM.sim_in.recv(28)
		control = list(struct.unpack('<14H', simbuf))
		pwm = control[:11]
		#(speed, direction, turbulance) = control[11:]

		#not quite sure why this is coming from th SITL....
		#global wind
		#wind.speed      = speed*0.01
		#wind.direction  = direction*0.01
		#wind.turbulance = turbulance*0.01

		self.controlServos.set_servos(pwm)
		#self.controlServos.servosPrint()
		#controlServos.servosPrint();
		#aileron  = (pwm[0]-1500)/500.0
		#elevator = (pwm[1]-1500)/500.0
		#throttle = (pwm[2]-1000)/1000.0
		#if opts.revthr:
		#	self.throttle = 1.0 - throttle
		#rudder   = (pwm[3]-1500)/500.0
		#control_state = control(aileron,rudder,throttle,elevator)
		#control_state.myprint();

	#state is of type fgFDM returns 
	def sendPacket(self,state):
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
		print (
			state.get('v_north', units='mps'),
			state.get('v_east', units='mps'),
			state.get('v_down', units='mps'))
		#simbuf = struct.pack('<17dI',37.61382276597417, -122.35788393026023, 13.569942677648676, 301.68819888465595, 13.466116415405274, -30.21166986694336, -9.254649060058593, -5.756516651916504, -0.050413392663002016, -11.137235311889649, -1.6254879057107736, 2.8957387399062418, -0.535181446767906, -1.7590227997395773, 12.431236280010225, 301.68819888465595, 21.707256408691407, 1280721231)
		try:
			APM.sim_out.send(simbuf)
		except:
			raise

##################
# main program
#localhost on the VM is 0.0.0.0 NOT 127.0.0.1 
#If you're UDP doesn't work, this is the issue
#Server: fgout (on the output)
from optparse import OptionParser
parser = OptionParser("runsimFG.py [options]")
parser.add_option("--simin",   help="SITL input (IP:port)",          default="127.0.0.1:5502")
parser.add_option("--simout",  help="SITL output (IP:port)",         default="127.0.0.1:5501")
parser.add_option("--fgout",   help="Output to FG (IP:port)",   default="0.0.0.0:5503")
parser.add_option("--fgin",   help="Input from FG (IP:port)",   default="0.0.0.0:5504")
parser.add_option("--options", type='string', help='jsbsim startup options')
parser.add_option("--elevon", action='store_true', default=False, help='assume elevon input')
parser.add_option("--revthr", action='store_true', default=False, help='reverse throttle')
parser.add_option("--vtail", action='store_true', default=False, help='assume vtail input')
parser.add_option("--wind", dest="wind", help="Simulate wind (speed,direction,turbulance)", default='0,0,0')

(opts, args) = parser.parse_args()

os.chdir(util.reltopdir('Tools/autotest'))


APM = SITLConnection(interpret_address(opts.simin), interpret_address(opts.simout))
FG = FGConnection(interpret_address(opts.fgin), interpret_address(opts.fgout))

global receivedST
global receivedFG


def mainLoop():
	receivedST = False
	receivedFG = False
	print("starting loop")
	while True:
		rin = [FG.fg_in.fileno(), APM.sim_in.fileno()]
		rout = [FG.fg_out.fileno(), APM.sim_out.fileno()]
		try:
			(rin, win, xin) = select.select(rin, rout, [], 0)
		except select.error:
			print("error")
			continue
		if FG.fg_in.fileno() in rin:
			print receivedFG
			receivedFG = True
			FG.readPacket()

		if APM.sim_in.fileno() in rin:
			receivedST = True
			APM.readPacket()

		if APM.sim_out.fileno() in rout:
			if receivedFG:
				APM.sendPacket(FG.fdm)

		if FG.fg_out.fileno() in rout:
			if receivedST:
				#APM.controlServos.servosPrint()
				#FG.sendPacket(APM.controlServos)
				#FG.printPacket()
				continue




mainLoop()


