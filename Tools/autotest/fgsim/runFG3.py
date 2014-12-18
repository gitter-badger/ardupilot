#!/usr/bin/env python
# run FlightGear Simulation

import sys, os, pexpect,socket, math, time, select, struct, signal, errno
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'pysim'))
import util, atexit, fdpexpect
from pymavlink import fgFDM
from optparse import OptionParser

global ground_height # removed from sitl_state since it should logically be independent
class basicLocation(object):
	def __init__(self,latitude,longitude,altitude,heading):
		self.latitude = latitude;
		self.longitude = longitude;
		self.altitude = altitude;
		self.heading = heading;

class control(object):
	def __init__(self,aileron,rudder,throttle,elevator):
		self.aileron = aileron;
		self.rudder = rudder;
		self.throttle = throttle;
		self.elevator = elevator;

class sitl_state(basicLocation, control):
	def __init__(self, start_control, start_location):
		self.aileron = start_control.aileron;
		self.rudder = start_control.rudder;
		self.throttle = start_control.throttle;
		self.elevator = start_control.elevator;

		self.latitude = start_location.latitude;
		self.longitude = start_location.longitude;
		self.altitude = start_location.altitude;
		self.heading = start_location.heading;

	def changeControl(self,newControl):
		'''takes in an instance of the control class'''
		self.aileron = newControl.aileron;
		self.rudder = newControl.rudder;
		self.throttle = newControl.throttle;
		self.elevator = newControl.elevator;

	def changeLocation(self,newLocation):
		'''takes in an instance of the location class'''
		self.latitude = newLocation.latitude;
		self.longitude = newLocation.longitude;
		self.altitude = newLocation.altitude;
		self.heading = newLocation.heading;

def classifyLocation(locationString):
	locationArray = locationString.split(',')
	lat = locationArray[0]
	lon = locationArray[1]
	alt = locationArray[2]
	head = locationArray[3]
	locationClass = location(lat,lon,alt,head)
	return locationClass

def classifyControl(controlString):
	'''turn string containing control info into instance of control class'''
	controlArray = controlString.split(',')
	ail = controlArray[0]
	rud = controlArray[1]
	thr = controlArray[2]
	elev = controlArray[3]
	controlClass = control(ail,rud,thr,elev)
	return controlClass

def interpret_address(addrstr):
    '''interpret a IP:port string'''
    a = addrstr.split(':')
    a[1] = int(a[1])
    return tuple(a)

def processFgInput(buf):
	fullState = fgFDM.fgFDM()
	print buf
	fullState.parse(buf)
	return fullState

def runArduOutput(currentFDM):
    newState = struct.pack('<17dI',
    	fdm.get('latitude', units='degrees'),
        fdm.get('longitude', units='degrees'),
        fdm.get('altitude', units='meters'),
        fdm.get('psi', units='degrees'),
	    fdm.get('v_north', units='mps'),
        fdm.get('v_east', units='mps'),
        fdm.get('v_down', units='mps'),
        fdm.get('A_X_pilot', units='mpss'),
	    fdm.get('A_Y_pilot', units='mpss'),
        fdm.get('A_Z_pilot', units='mpss'),
        fdm.get('phidot', units='dps'),
        fdm.get('thetadot', units='dps'),
        fdm.get('psidot', units='dps'),
        fdm.get('phi', units='degrees'),
        fdm.get('theta', units='degrees'),
        fdm.get('psi', units='degrees'),
        fdm.get('vcas', units='mps'),
        0x4c56414f)
    run_to_ardu.send(newState)

def processArduInput(buffer):
	controlSurfaces = list(struct.unpack('<14H', buf))
	surfaces = controlSurfaces[:11]
	aileron  = (surfaces[0]-1500)/500.0
    elevator = (surfaces[1]-1500)/500.0
    throttle = (surfaces[2]-1000)/1000.0
    rudder   = (surfaces[3]-1500)/500.0
    newControls = control(aileron, rudder, throttle, elevator)
    return newControls

def runFgOutput(currentControls):
	newControls = struct.pack()



##################### main program #################################
parser = OptionParser("runFG3.py [options]")
parser.add_option("--startLocation", help="Beginning Location of Aircraft", default="0,0,0,0")
parser.add_option("--startControl", help="Beginning control surfaces of Aircraft", default="1500,1500,1000,1500")
parser.add_option("--arduRun", help="Input port from ArduPilot", default="127.0.0.1:5502")
parser.add_option("--runArdu", help="Output port to ArduPilot", default="127.0.0.1:5501")
parser.add_option("--runFg", help="Output port to FlightGear", default="127.0.0.1:6502")
parser.add_option("--fgRun", help="Input port from FlightGear", default="127.0.0.1:6501")

(opts, args) = parser.parse_args()

initControl = classifyControl(opts.startControl)
initLocation = classifyLocation(opts.startLocation)
current_state = sitl_state(initControl,initLocation)

# os.chdir('/vagrant')
# cmd = "fgfs --model-hz=1000"
# cmd = cmd + " --lon=" + initLocation.longitude + " --lat=" + initLocation.latitude + " --altitude=" + initLocation.altitude + " --heading=" + initLocation.heading
# cmd = cmd + " --generic=socket,out,40,localhost,6501,udp,MAVLink" + "--generic=socket,in,45,localhost,6502,udp,MAVLink"
# fg = pexpect.spawn(cmd, timeout=10)
# fg.delaybeforespend = 0

run_to_ardu_address = interpret_address(opts.runArdu)
ardu_to_run_address  = interpret_address(opts.arduRun)
fg_to_run_address = interpret_address(opts.fgRun)
run_to_fg_address = interpret_address(opts.runFg)

ardu_to_run = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ardu_to_run.connect(ardu_to_run_address)

run_to_ardu = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
run_to_ardu.bind(run_to_ardu_address)

fg_to_run = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fg_to_run.connect(fg_to_run_address)

run_to_fg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
run_to_fg.bind(run_to_fg_address)

print 'ready to fly'

def main_loop():
	now = time.time()
	last_report = now
	while True:
		now = time.time()

		fgRunInput = fg_to_run.recv(8192)
		processedFgRunInput = processFgInput(fgRunInput) ### parse buffer and create fdm ###
		runArduOutput(processedFgRunInput) ### send fdm elements ####

		arduRunInput = ardu_to_run.recv(8192)
		processedArduRunInput = processArduInput(arduRunInput) ### parse buffer and create control state instance ###
		runFgOutput(processedArduRunInput) ### send control state back to flightgear ###


        '''
        if tnow - last_report > 3:
            print("asl=%.1f agl=%.1f roll=%.1f pitch=%.1f a=(%.2f %.2f %.2f)" % (
                fdm.get('altitude', units='meters'),
                fdm.get('agl', units='meters'),
                fdm.get('phi', units='degrees'),
                fdm.get('theta', units='degrees'),
                fdm.get('A_X_pilot', units='mpss'),
                fdm.get('A_Y_pilot', units='mpss'),
                fdm.get('A_Z_pilot', units='mpss')))
            last_report = time.time()
        '''
main_loop()




















