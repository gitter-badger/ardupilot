#!/bin/bash

# Try to run a command in an appropriate type of terminal window
# depending on whats available
# Sigh: theres no common way of handling command line args :-(


name="$1"
shift
echo "Starting with Screen $name : $*"
# default to xterm as it has the most consistent options and can start minimised
if [ -x /usr/bin/xterm ]; then
  /usr/bin/xterm -n "$name" -name "$name" -T "$name" -hold -e $* &
elif [ -x /usr/bin/konsole ]; then
  /usr/bin/konsole --hold -e $*
elif [ -x /usr/bin/gnome-terminal ]; then
  /usr/bin/gnome-terminal -e "$*"
elif [ -n "$STY" ]; then
  # We are running inside of screen, try to start it there
  /usr/bin/screen -X screen -t $name $*
else
  #screen -X -S $name quit
  #screen -S $name -dm $*
  nice tmux -c "$*"
  echo "ERROR: Please install xterm"
  exit 1
fi
exit 0
