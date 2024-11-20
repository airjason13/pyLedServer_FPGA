#!/bin/sh

export DISPLAY=:0
COUNT=0
while :
do
	xdotool windowactivate $(xdotool search --title http) &&
	xdotool key "ctrl+F5" &&	
	xdotool windowactivate $(xdotool search --title http)
	xdotool mousemove 1280 720
	COUNT=$((COUNT+1))
	echo $COUNT >> /home/root/refresh_chromium_count.dat
	sleep 300

done
