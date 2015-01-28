#ArduPilot Project#

### The ArduPilot project is made up of: ###
>>ArduCopter (or APM:Copter) : [code](https://github.com/diydrones/ardupilot/tree/master/ArduCopter), [wiki](http://copter.ardupilot.com)

>>ArduPlane (or APM:Plane) : [code](https://github.com/diydrones/ardupilot/tree/master/ArduPlane), [wiki](http://plane.ardupilot.com)

>>ArduRover (or APMrover2) : [code](https://github.com/diydrones/ardupilot/tree/master/APMrover2), [wiki](http://rover.ardupilot.com)

>>Antenna Tracker : [code](https://github.com/diydrones/ardupilot/tree/master/AntennaTracker), [wiki](http://copter.ardupilot.com/wiki/common-antennatracker-introduction)

##How to get FlightGear Simulation Running##
1. Statup vagrant using the vagrantfile provided
2. Add fgfs to your path
2a. Move the MAVLink.xml file in Tools/autotest/jsmsim to Flightgear/Resorces/data/Protocol
3. On the VM go to ArduPlane and run sim_FG.sh
4. Run sh ardupilot/Tools/autotest/sim_fg_host.sh on the host
5. NOTE: If you can't run this, run chmod 777 sim_fg_host.sh first
6. Starts the plane in the air. If it ardu dies, pause flightgear (type p) then 
restart ardu (by running sim_FG.sh again) then unpause flightgear (type p)




### License ###
>>[Overview of license](http://dev.ardupilot.com/wiki/license-gplv3)

>>[Full Text](https://github.com/diydrones/ardupilot/blob/master/COPYING.txt)
