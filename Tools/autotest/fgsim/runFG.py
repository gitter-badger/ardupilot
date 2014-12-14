#!/usr/bin/env/python
# run a FG model as a child process

import sys, os, pexpect, socket
import math, time, select, struct, signal, errno

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'pysim'))
import util, atexit, fdpexpect
from pymavlink import fgFDM

class control_state(object):
    def __init__(self):
        self.aileron = 0
        self.elevator = 0
        self.throttle = 0
        self.rudder = 0
        self.ground_height = 0

sitl_state = control_state()

def interpret_address(addrstr):
    '''interpret a IP:port string'''
    a = addrstr.split(':')
    a[1] = int(a[1])
    return tuple(a)

def setup_initial(home):
	global opts
    if len(home) != 4:
        print("home should be lat,lng,alt,hdg - '%s'" % home)
        sys.exit(1)
    latitude = float(home[0])
    longitude = float(home[1])
    altitude = float(home[2])
    heading = float(home[3])
    sitl_state.ground_height = altitude

def process_sitl_input(buf):
    '''process control changes from SITL sim'''
    control = list(struct.unpack('!14H', buf))
    aileron  = (pwm[0]-1500)/500.0
    elevator = (pwm[1]-1500)/500.0
    throttle = (pwm[2]-1000)/1000.0
    rudder   = (pwm[3]-1500)/500.0
    if aileron != sitl_state.aileron:
        sitl_state.aileron = aileron
    if elevator != sitl_state.elevator:
        sitl_state.elevator = elevator
    if rudder != sitl_state.rudder:
        sitl_state.rudder = rudder
    if throttle != sitl_state.throttle:
        sitl_state.throttle = throttle

def process_input(buf):
    '''process FG FDM input from JSBSim'''
    global fdm, sim_out
    fdm.parse(buf)

    simbuf = struct.pack('<17dI',
                         fdm.get('latitude', units='degrees'),
                         fdm.get('longitude', units='degrees'),
                         fdm.get('altitude', units='meters'),
                         fdm.get('heading', units='degrees'),
                         fdm.get('v_north', units='mps'),
                         fdm.get('v_east', units='mps'),
                         fdm.get('v_down', units='mps'),
                         fdm.get('ax', units='mpss'),
                         fdm.get('ay', units='mpss'),
                         fdm.get('az', units='mpss'),
                         fdm.get('p-body', units='dps'),
                         fdm.get('q-body', units='dps'),
                         fdm.get('r-body', units='dps'),
                         fdm.get('roll', units='degrees'),
                         fdm.get('pitch', units='degrees'),
                         fdm.get('yaw', units='degrees'),
                         fdm.get('vcas', units='mps'),
                         0x4c56414f)
    try:
        sim_out.send(simbuf)
    except socket.error as e:
        print e
        if e.errno not in [ errno.ECONNREFUSED ]:
            raise


############### main program ##############################
from optparse import OptionParser
parser = OptionParser("runFG.py [options]")
parser.add_option("--simin", help="SITL input (IP:port)")
parser.add_option("--simout",  help="SITL output (IP:port)")
parser.add_option("--options", type='string', help='flightgear startup options')
(opts, args) = parser.parse_args()

os.chdir(util.reltopdir('Tools/autotest'))
atexit.register(util.pexpect_close_all)

setup_initial([10,10,0,0]);

cmd = "FlightGear"
fg = pexpect.spawn(cmd, logfile=sys.stdout, timeout=10)
fg.delaybeforesend = 0
util.pexpect_autoclose(fg)
i = fg.expect(["Successfully bound to socket for input on port (\d+)",
                "Could not bind to socket for input"])
if i == 1:
    print("Failed to start FlightGear - is another copy running?")
    sys.exit(1)

# socket addresses
sim_out_address = interpret_address(opts.simout)
sim_in_address  = interpret_address(opts.simin)

# setup input from SITL sim
sim_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sim_in.bind(sim_in_address)
sim_in.setblocking(0)

# setup output to SITL sim
sim_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sim_out.connect(interpret_address(opts.simout))
sim_out.setblocking(0)

print("Simulator ready to fly")

def main_loop():
    '''run main loop'''
    tnow = time.time()
    last_sim_input = tnow
    paused = False

    while True:
    	rin = [sim_in.fileno(), fg.fileno()]
        try:
            (rin, win, xin) = select.select(rin, [], [], 1.0)
        except select.error:
            util.check_parent()
            continue
    	tnow = time.time;
        if sim_in.fileno() in rin:
            buf = sim_in.recv(17*8+4)
            process_input(buf)

        if tnow - last_sim_input > 0.2:
            if not paused:
                print("PAUSING SIMULATION")
                paused = True
        else:
            if paused:
                print("RESUMING SIMULATION")
                paused = False

        if tnow - last_report > 3:
            print("alt=%.1f roll=%.1f pitch=%.1f a=(%.2f %.2f %.2f)" % (
                fdm.get('altitude', units='meters'),
                fdm.get('roll', units='degrees'),
                fdm.get('pitch', units='degrees'),
                fdm.get('ax', units='mpss'),
                fdm.get('ay', units='mpss'),
                fdm.get('az', units='mpss')))





















