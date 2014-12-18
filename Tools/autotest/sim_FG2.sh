#!/bin/bash

# home location lat, lon, alt, heading
LOCATION="CMAC"
VEHICLE=""
BUILD_TARGET="sitl"
NUM_PROCS=1

# check the instance number to allow for multiple copies of the sim running at once
INSTANCE=0
CLEAN_BUILD=0
WIPE_EEPROM=0
NO_REBUILD=0
START_HIL=0
EXTERNAL_SIM=0

usage()
{
cat <<EOF
Usage: sim_vehicle.sh [options] [mavproxy_options]
Options:
    -v VEHICLE       vehicle type (ArduPlane, ArduCopter or APMrover2)
                     vehicle type defaults to working directory
    -I INSTANCE      instance of simulator (default 0)
    -L               select start location from Tools/autotest/locations.txt
    -c               do a make clean before building
    -N               don't rebuild before starting ardupilot
    -w               wipe EEPROM and reload parameters
    -j NUM_PROC      number of processors to use during build (default 1)
    -H               start HIL
    -e               use external simulator

mavproxy_options:
    --console        start with a status console
    --out DEST       start MAVLink output to DEST

Note: 
    eeprom.bin in the starting directory contains the parameters for your 
    simulated vehicle. Always start from the same directory. It is recommended that 
    you start in the main vehicle directory for the vehicle you are simulating, 
    for example, start in the ArduPlane directory to simulate ArduPlane
EOF
}


# parse options. Thanks to http://wiki.bash-hackers.org/howto/getopts_tutorial
while getopts ":I:Vcj:L:v:w:NHe" opt; do
  case $opt in
    v)
      VEHICLE=$OPTARG
      ;;
    I)
      INSTANCE=$OPTARG
      ;;
    N)
      NO_REBUILD=1
      ;;
    H)
      START_HIL=1
      NO_REBUILD=1
      ;;
    L)
      LOCATION="$OPTARG"
      ;;
    c)
      CLEAN_BUILD=1
      ;;
    j)
      NUM_PROCS=$OPTARG
      ;;
    w)
      WIPE_EEPROM=1
      ;;
    e)
      EXTERNAL_SIM=1
      ;;
    \?)
      # allow other args to pass on to mavproxy
      break
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
  esac
done
shift $((OPTIND-1))

# kill existing copy if this is the '0' instance only
kill_tasks() 
{
    [ "$INSTANCE" -eq "0" ] && {
        killall -q JSBSim lt-JSBSim ArduPlane.elf fgfs
        pkill -f runsim.py runFG2.py
    }
}

kill_tasks

trap kill_tasks SIGINT

# setup ports for this instance
MAVLINK_PORT="tcp:127.0.0.1:5760"
ARDU_TO_RUN="127.0.0.1:5502"
RUN_TO_ARDU="127.0.0.1:5501"

RUN_TO_FG="127.0.0.1:6502"
FG_TO_RUN="127.0.0.1:6501"

set -x

VEHICLE="ArduPlane"

autotest=$(dirname $(readlink -e $0))
if [ $NO_REBUILD == 0 ]; then
pushd $autotest/../../$VEHICLE || {
    echo "Failed to change to vehicle directory for $VEHICLE"
    usage
    exit 1
}
if [ $CLEAN_BUILD == 1 ]; then
    make clean
fi
make $BUILD_TARGET -j$NUM_PROCS || {
    make clean
    make $BUILD_TARGET -j$NUM_PROCS
}
popd
fi

# get the location information
SIMHOME=$(cat $autotest/locations.txt | grep -i "^$LOCATION=" | cut -d= -f2)
[ -z "$SIMHOME" ] && {
    echo "Unknown location $LOCATION"
    usage
    exit 1
}

echo "Starting up at $LOCATION : $SIMHOME"

SIMCONTROLS="0,0,0,0"

cmd="/tmp/$VEHICLE.build/$VEHICLE.elf -I$INSTANCE"
if [ $WIPE_EEPROM == 1 ]; then
    cmd="$cmd -w"
fi


RUNSIM="python $autotest/fgsim/runFG3.py --startLocation=$SIMHOME --startControl=$SIMCONTROLS --arduRun=$ARDU_TO_RUN --runArdu=$ARDU_TO_RUN --runFg=$RUN_TO_FG --fgRun=$FG_TO_RUN"
PARMS="ArduPlane.parm"
if [ $WIPE_EEPROM == 1 ]; then
  cmd="$cmd -PFORMAT_VERSION=13 -PSKIP_GYRO_CAL=1 -PRC3_MIN=1000 -PRC3_TRIM=1000"
fi

$autotest/run_in_terminal_window.sh "ardupilot" $cmd || exit 1

trap kill_tasks SIGINT

sleep 2
rm -f $tfile
if [ $EXTERNAL_SIM == 0 ]; then
    $autotest/run_in_terminal_window.sh "Simulator" $RUNSIM || {
        echo "Failed to start simulator: $RUNSIM"
        exit 1
    }
    sleep 2
else
    echo "Using external simulator"
fi

options=""
if [ $START_HIL == 0 ]; then
options="--master $MAVLINK_PORT --sitl $SIMOUT_PORT"
fi
options="$options --out 127.0.0.1:14550 --out 127.0.0.1:14551"
if [ $WIPE_EEPROM == 1 ]; then
    extra_cmd="param forceload $autotest/$PARMS; param fetch"
fi
mavproxy.py $options --cmd="$extra_cmd" $*
echo "Hit return to continue"
read not_matter
kill_tasks
