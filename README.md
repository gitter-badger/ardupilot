#ArduPilot Project#

[![Join the chat at https://gitter.im/CUAir/ardupilot](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/CUAir/ardupilot?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/diydrones/ardupilot?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

### The ArduPilot project is made up of: ###
>>ArduCopter (or APM:Copter) : [code](https://github.com/diydrones/ardupilot/tree/master/ArduCopter), [wiki](http://copter.ardupilot.com)

>>ArduPlane (or APM:Plane) : [code](https://github.com/diydrones/ardupilot/tree/master/ArduPlane), [wiki](http://plane.ardupilot.com)

>>ArduRover (or APMrover2) : [code](https://github.com/diydrones/ardupilot/tree/master/APMrover2), [wiki](http://rover.ardupilot.com)

>>Antenna Tracker : [code](https://github.com/diydrones/ardupilot/tree/master/AntennaTracker), [wiki](http://copter.ardupilot.com/wiki/common-antennatracker-introduction)

##How to get FlightGear Simulation Running##
1. Statup vagrant using the vagrantfile provided
2. Add fgfs to your path
2a. Move the MAVLink.xml file in Tools/autotest/jsbsim to Flightgear/Resorces/data/Protocol
2b. Make the ardubuilds folder and set the permissions to 777
3. Run sh ardupilot/Tools/autotest/sim_fg_host.sh on the host
3a. NOTE: If you can't run this, run chmod 777 sim_fg_host.sh first
3b. Press (p) to pause the sim
4. On the VM go to ArduPlane and run sim_FG.sh
5. Connect to the Autopilot on the host through 127.0.0.1:5555
5a. This can be done through APM Planner or MAVProxy
6. Unpause FlightGear by pressing (p)
7. To kill ardupilote, do control-C then press enter




### License ###
>>[Overview of license](http://dev.ardupilot.com/wiki/license-gplv3)

>>[Full Text](https://github.com/diydrones/ardupilot/blob/master/COPYING.txt)
