#!/usr/bin/env python
# run a jsbsim model as a child process

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

def jsb_set(variable, value):
    '''set a JSBSim variable'''
    global jsb_console
    jsb_console.send('set %s %s\r\n' % (variable, value))

def setup_template(home):
    '''setup aircraft/EasyStar/reset00.xml'''
    global opts
    v = home.split(',')
    if len(v) != 4:
        print("home should be lat,lng,alt,hdg - '%s'" % home)
        sys.exit(1)
    latitude = float(v[0])
    longitude = float(v[1])
    altitude = float(v[2])
    heading = float(v[3])
    sitl_state.ground_height = altitude
    

def process_sitl_input(buf):
    '''process control changes from SITL sim'''
    control = list(struct.unpack('<14H', buf))
    pwm = control[:11]
    (speed, direction, turbulance) = control[11:]
    
    aileron  = (pwm[0]-1500)/500.0
    elevator = (pwm[1]-1500)/500.0
    throttle = (pwm[2]-1000)/1000.0
    rudder   = (pwm[3]-1500)/500.0
        
    sitl_state.aileron = aileron
    sitl_state.elevator = elevator
    sitl_state.rudder = rudder
    sitl_state.throttle = throttle
    
def process_jsb_input(buf):
    '''process FG FDM input from JSBSim'''
    global fdm, fg_out, sim_out
    fdm.parse(buf)
    simbuf = struct.pack('<17dI',
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
    try:
        sim_out.send(simbuf)
    except socket.error as e:
        if e.errno not in [ errno.ECONNREFUSED ]:
            raise



##################
# main program
from optparse import OptionParser
parser = OptionParser("runsim.py [options]")
parser.add_option("--simin",   help="SITL input (IP:port)",          default="127.0.0.1:5502")
parser.add_option("--simout",  help="SITL output (IP:port)",         default="127.0.0.1:5501")
parser.add_option("--fgout",   help="FG display output (IP:port)",   default="127.0.0.1:5503")
parser.add_option("--home",    type='string', help="home lat,lng,alt,hdg (required)")
parser.add_option("--script",  type='string', help='jsbsim model script', default='jsbsim/easystar_test.xml')
parser.add_option("--options", type='string', help='jsbsim startup options')

(opts, args) = parser.parse_args()

for m in [ 'home', 'script' ]:
    if not opts.__dict__[m]:
        print("Missing required option '%s'" % m)
        parser.print_help()

os.chdir(util.reltopdir('Tools/autotest'))

# kill off child when we exit
atexit.register(util.pexpect_close_all)

setup_template(opts.home)

# start child
cmd = "JSBSim --realtime --suspend --nice --simulation-rate=1000 --logdirectivefile=jsbsim/fgout.xml --script=jsbsim/easystar_test.xml"
if opts.options:
    cmd += ' %s' % opts.options

jsb = pexpect.spawn(cmd, logfile=sys.stdout, timeout=10)
jsb.delaybeforesend = 0
util.pexpect_autoclose(jsb)
i = jsb.expect(["Successfully bound to socket for input on port (\d+)",
                "Could not bind to socket for input"])
if i == 1:
    print("Failed to start JSBSim - is another copy running?")
    sys.exit(1)
jsb_out_address = interpret_address("127.0.0.1:%u" % int(jsb.match.group(1)))
jsb.expect("Creating UDP socket on port (\d+)")
jsb_in_address = interpret_address("127.0.0.1:%u" % int(jsb.match.group(1)))
jsb.expect("Successfully connected to socket for output")
jsb.expect("JSBSim Execution beginning")

# setup output to jsbsim
print("JSBSim console on %s" % str(jsb_out_address))
jsb_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
jsb_out.connect(jsb_out_address)
jsb_console = fdpexpect.fdspawn(jsb_out.fileno(), logfile=sys.stdout)
jsb_console.delaybeforesend = 0

# setup input from jsbsim
print("JSBSim FG FDM input on %s" % str(jsb_in_address))
jsb_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
jsb_in.bind(jsb_in_address)
jsb_in.setblocking(0)

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

# setup possible output to FlightGear for display
fg_out = None
if opts.fgout:
    fg_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fg_out.connect(interpret_address(opts.fgout))



fdm = fgFDM.fgFDM()

jsb_console.send('info\n')
jsb_console.send('resume\n')
jsb.expect(["trim computation time","Trim Results"])
time.sleep(1.5)
jsb_console.logfile = None

print("Simulator ready to fly")

def main_loop():
    '''run main loop'''
    tnow = time.time()
    last_report = tnow
    last_sim_input = tnow
    paused = False

    while True:
        rin = [jsb_in.fileno(), sim_in.fileno(), jsb_console.fileno(), jsb.fileno()]
        try:
            (rin, win, xin) = select.select(rin, [], [], 1.0)
        except select.error:
            util.check_parent()
            continue

        tnow = time.time()

        if jsb_in.fileno() in rin:
            buf = jsb_in.recv(fdm.packet_size())
            process_jsb_input(buf)

        if sim_in.fileno() in rin:
            simbuf = sim_in.recv(28)
            process_sitl_input(simbuf)
            last_sim_input = tnow

        # show any jsbsim console output
        if jsb_console.fileno() in rin:
            util.pexpect_drain(jsb_console)
        if jsb.fileno() in rin:
            util.pexpect_drain(jsb)

        if tnow - last_sim_input > 0.2:
            if not paused:
                print("PAUSING SIMULATION")
                paused = True
        else:
            if paused:
                print("RESUMING SIMULATION")
                paused = False

        # only simulate wind above 5 meters, to prevent crashes while
        # waiting for takeoff

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

def exit_handler():
    '''exit the sim'''
    print("HELP I'm DYING")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    # JSBSim really doesn't like to die ...
    if getattr(jsb, 'pid', None) is not None:
        os.kill(jsb.pid, signal.SIGKILL)
    jsb_console.send('quit\n')
    jsb.close(force=True)
    util.pexpect_close_all()
    sys.exit(1)

signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

try:
    main_loop()
except:
    exit_handler()
    raise
