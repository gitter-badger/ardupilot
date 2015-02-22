#!/bin/sh

AUTOTESTDIR=$(dirname $0)

fgfs \
	--native-fdm=socket,out,40,127.0.0.1,5514,udp \
	--generic=socket,in,40,127.0.0.1,5503,udp,MAVLink \
	--wind=0@10 \
	--httpd=5400 \
	--timeofday=noon \
	--fg-aircraft="$AUTOTESTDIR/aircraft" \
	--aircraft=easystar\
	--altitude=6 \
	--vc=100 \

	--enable-freeze \
    $*
    #--aircraft=Rascal110-JSBSim \