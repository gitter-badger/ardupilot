#!/usr/bin/env python

'''Test to see if we can communicate with XPlane. 
'''
import sys, os, pexpect, socket
import math, time, select, struct, signal, errno

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'pysim'))

def interpret_address(addrstr):
	'''interpret a IP:port string'''
	a = addrstr.split(':')
	a[1] = int(a[1])
	return tuple(a)

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


class xParser(object):
	def __init__(self):
		self.unpacked = 0
		self.length = 7
		self.sim_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sim_in.bind(('127.0.0.1',49005))
		self.sim_in.setblocking(0)
		self.sim_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sim_out.connect(('0.0.0.0',49000))
		self.sim_out.setblocking(0)
	#The mapping to find the location
	#mapping works (array ind in packet, offset from ind, 'unit')
	#The regular packet is in the form 4,6,16,17,20,21
	items = {
	'lat':(45,1,'deg'), #9*5
	'lon':(45,2,'deg'),
	'alt':(45,4,'ft'), #note: above ground level
	'v_north':(54,6,'m/s'), #9*6  #this is v_Z in xPlane, with forward as -
	'v_east':(54,4,'m/s'), #this is v_X in xPlane, with right as -
	'v_down':(54,5,'m/s'), #this is v_Y in xPlane, with down as -
	'A_X_pilot':(9,6,'Gs'), #9*1
	'A_Y_pilot':(9,7,'Gs'),
	'A_Z_pilot':(9,5,'Gs'),
	'phidot':(27,2,'rad/s'), #9*3
	'thetadot':(27,1,'rad/s'),
	'psidot':(27,3,'rad/s'),
	'phi':(36,2,'deg'), #9*4
	'theta':(36,1,'deg'),
	'psi':(36,3,'deg'), #Heading
	'vcas':(0,6,'mph'), #Airspeed, 9*0
	}

	#Converts from first unit to second unit
	converterList = {
	('mph','m/s'):0.44704,
	('Gs','m/s2'):-9.80665,
	('ft','m'):0.3048,
	('deg','rad'):0.0174532925,
	('rad','deg'):57.2957795,
	('rad/s', 'deg/s'):57.2957795
	}

	def parse(self, packet, length):
		unPackstr = '<ccccx'
		for i in range(0,length):
			unPackstr += 'Iffffffff'
		self.unpacked = list(struct.unpack(unPackstr, packet))
		return self.unpacked

	def parseReg(self, packet):
		self.parse(packet, self.length)

	def getItem(self,itm,unt):
		find = self.items.get(itm)
		val = self.unpacked[4+find[0]+find[1]]
		return self.converter(val,find[2],unt)

	def converter(self, value, unt1, unt2):
		if (unt1==unt2):
			return value
		return self.converterList.get((unt1,unt2))*value

	def buildPacket(self,servControl):
		#elev: 11, 1
		#ailrn: 11, 2
		#rudder: 11, 3
		#Throttle: 25, 1
		elev = servControl.ch2
		ailrn = servControl.ch1
		rud = servControl.ch4
		throt = 0#servControl.ch3
		header = ['D','A','T','A',1]
		surfaces = [11,elev,ailrn,rud,-999.0,-999.0,-999.0,-999.0,-999.0]
		#throttle = [25,throt,-999.0,-999.0,-999.0,-999.0,-999.0,-999.0,-999.0]
		data = header + surfaces #+ throttle
		return struct.pack('<ccccBIffffffff',*data)

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

	#state is of type xParser returns 
	def sendPacket(self,state):
		simbuf = struct.pack('<17dI',
			state.getItem('lat', 'deg'),
			state.getItem('lon', 'deg'),
			state.getItem('alt', 'm'),
			0,#state.getItem('psi', 'deg'), #heading
			0,#state.getItem('v_north', 'm/s')*-1.0, #forward speed
			0,#state.getItem('v_east', 'm/s'),
			0,#state.getItem('v_down', 'm/s')*-1.0,
			state.getItem('A_X_pilot', 'm/s2')*-1.0, #pitch (- is lean forward)
			0,#state.getItem('A_Y_pilot', 'm/s2'), #roll (- is lean left)
			state.getItem('A_Z_pilot', 'm/s2'),
			0,#state.getItem('phidot', 'deg/s'), #roll
			state.getItem('thetadot', 'deg/s'), #pitch
			0, #state.getItem('psidot', 'deg/s'),
			0,#state.getItem('phi', 'deg'),
			0,#state.getItem('theta', 'deg'),
			0,#state.getItem('psi', 'deg'),
			state.getItem('vcas', 'm/s'),
			0x4c56414f) 
		#simbuf = struct.pack('<17dI',37.61382276597417, -122.35788393026023, 13.569942677648676, 301.68819888465595, 13.466116415405274, -30.21166986694336, -9.254649060058593, -5.756516651916504, -0.050413392663002016, -11.137235311889649, -1.6254879057107736, 2.8957387399062418, -0.535181446767906, -1.7590227997395773, 12.431236280010225, 301.68819888465595, 21.707256408691407, 1280721231)
		#print (state.getItem('A_X_pilot', 'm/s2'),state.getItem('A_Y_pilot', 'm/s2'))
		try:
			APM.sim_out.send(simbuf)
		except:
			return 0
		return 1



XParser = xParser()
APM = SITLConnection(('127.0.0.1',5502),('127.0.0.1',5501))

def mainLoop():
	receivedST = False
	receivedXP = False

# There are 41 bytes per sentence
# The first 5 bytes are the message header, or "prolouge"
# First 4 of the 5 prolouge bytes are the message type, like "DATA"
# Fifth byte of prolouge is an "internal-use" byte
# The next 36 bytes are the message
# First 4 bytes of message indicates the index number of a data element, as shown in the Data Output screen in X-Plane
# Last 32 bytes is the data, up to 8 single-precision floating point numbers
# Therefore lets create the packet decoding as such:
# Header: <ccccx
# Data: 
	# Index: <I
	# Data: <ffffffff
	while(True):
		rin = [XParser.sim_in, APM.sim_in]
		rout = [XParser.sim_out, APM.sim_out]
		try:
			(rin, wout, xin) = select.select(rin, rout, [], 0)
		except select.error:
			print("error")
			continue
		if XParser.sim_in in rin:
			receivedXP = True
			simbuf = XParser.sim_in.recv(5+36*7)
			XParser.parseReg(simbuf)
		if APM.sim_in in rin:
			receivedST = True
			APM.readPacket()
		if APM.sim_out in wout:
			if receivedXP:
				APM.sendPacket(XParser)
		if XParser.sim_out in wout:
			if receivedST:
				data = XParser.buildPacket(APM.controlServos)
				#XParser.sim_out.send(data)
mainLoop()

#(37.61382276597417, -122.35788393026023, 13.569942677648676, 301.68819888465595, 13.466116415405274, -30.21166986694336, -9.254649060058593, -5.756516651916504, -0.050413392663002016, -11.137235311889649, -1.6254879057107736, 2.8957387399062418, -0.535181446767906, -1.7590227997395773, 12.431236280010225, 301.68819888465595, 21.707256408691407, 1280721231)
#(32.011512756347656, -91.7591781616211, 0.02059161874651909, 93.84944152832031, 0.0, 7.013537469902076e-06, 0.0, 9.803473123529553, -9796.84335, -0.0002968105758236561, -0.0008166327207061195, 0.0008762404410860017, 0.0, 0.3831479251384735, 0.3036905527114868, 93.84944152832031, 4.115508289714853e-08, 1280721231)

