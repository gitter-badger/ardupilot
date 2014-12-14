#ArduPilot Project#

### The ArduPilot project is made up of: ###
>>ArduCopter (or APM:Copter) : [code](https://github.com/diydrones/ardupilot/tree/master/ArduCopter), [wiki](http://copter.ardupilot.com)

>>ArduPlane (or APM:Plane) : [code](https://github.com/diydrones/ardupilot/tree/master/ArduPlane), [wiki](http://plane.ardupilot.com)

>>ArduRover (or APMrover2) : [code](https://github.com/diydrones/ardupilot/tree/master/APMrover2), [wiki](http://rover.ardupilot.com)

>>Antenna Tracker : [code](https://github.com/diydrones/ardupilot/tree/master/AntennaTracker), [wiki](http://copter.ardupilot.com/wiki/common-antennatracker-introduction)

### How to get Flightgear simulation running (Does not currently work) ###
>Please note, this assumes your copy of ardupilot is in a vagrant virtualbox under /vagrant/ardupilot

>Also, make sure your vagrantfile works similarly (port forwarding, etc.) to the one in the home directory of this repository

>First, open flight gear
>>Option 1: open the flightgear launcher application and in "Others" tab, paste "--generic=socket,out,100,localhost,5501,udp,MAVLink --generic=socket,in,100,localhost,5502,udp,MAVLink" (without the quotation marks)

>>Option 2: enter the following command into terminal (assumes Flightgear Launcher app is in /Applications)
>>>/Applications/Flightgear.app/Contents/MacOS/fgfs --generic=socket,out,100,localhost,5501,udp,MAVLink --generic=socket,in,100,localhost,5502,udp,MAVLink

>Then in a separate terminal within your vagrant shell, navigate to this directory (ardupilot) then execute the following commands

>>cd Tools/autotest

>>sim_FG.sh -w

>>>The -w is only necessary on first run to wipe params

>>>You may also use -j NUMPROC where NUMPROC is the number of processers you have to speed up compiling


### How to connect to MAVProxy (Does currently work) ###
>Please note, this assumes your copy of ardupilot is in a vagrant virtualbox under /vagrant/ardupilot

>Navigate to this directory (ardupilot), then execute the following commands
>>cd Tools/autotest

>>sim_FG.sh -w

>>>The -w is only necessary on first run to wipe params

>>>You may also use -j NUMPROC where NUMPROC is the number of processers you have to speed up compiling


>When the windows load, go back to the terminal and enter the following:
>>module load console

>>wp load /vagrant/ardupilot/Tools/autotest/ArduPlane-Missions/CMAC-toff-loop.txt

>>>This won't actually make the plane fly since communication with FG is not functional, but it is evidence of connection with MAVProxy




### User Support & Discussion Forums ###
>>APM Forum: [http://ardupilot.com/forum/index.php](http://ardupilot.com/forum/index.php)

>>Community Site: [http://diydrones.com](http://diydrones.com)

### Developer Information ###
>>Github repository: [https://github.com/diydrones/ardupilot](https://github.com/diydrones/ardupilot)

>>Main developer wiki: [http://dev.ardupilot.com](http://dev.ardupilot.com)

>>Developer email group: drones-discuss@googlegroups.com

### Contributors ###
>>[Github statistics](https://github.com/diydrones/ardupilot/graphs/contributors)

### How To Get Involved ###
>>The ArduPilot project is open source and we encourage participation and code contributions: [guidelines for contributors to the ardupilot codebase](http://dev.ardupilot.com/wiki/guidelines-for-contributors-to-the-apm-codebase)

>>We have an active group of Beta Testers especially for ArduCopter to help us find bugs: [release procedures](http://dev.ardupilot.com/wiki/release-procedures)

>>Desired Enhancements and Bugs can be posted to the [issues list](https://github.com/diydrones/ardupilot/issues).

>>Helping other users with log analysis on [diydrones.com](http://www.diydrones.com) and the [APM forums ](http://ardupilot.com/forum/index.php) is always appreciated:

>>There is a group of wiki editors as well in case documentation is your thing: ardu-wiki-editors@googlegroups.com

>>Developer discussions occur on drones-discuss@google-groups.com

### License ###
>>[Overview of license](http://dev.ardupilot.com/wiki/license-gplv3)

>>[Full Text](https://github.com/diydrones/ardupilot/blob/master/COPYING.txt)
