#!/bin/sh

AUTOTESTDIR=$(dirname $0)

fgfs \
	--native-fdm=socket,out,40,127.0.0.1,5514,udp \
	--generic=socket,in,40,127.0.0.1,5503,udp,MAVLink \
	--wind=0@0 \
	--httpd=5400 \
	--timeofday=noon \
	--fg-aircraft="$AUTOTESTDIR/aircraft" \
	--aircraft=Rascal110-JSBSim \
	#--altitude=10000 \
	#--vc=100 \

	--enable-freeze \
    $*