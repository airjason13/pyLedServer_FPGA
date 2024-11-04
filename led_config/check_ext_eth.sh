#!/bin/sh
NETWORK_FAIL_COUNT=0
NETWORK_FAIL_MAX_COUNT=50

while :
do
	echo "check eth dongle alive or not!@"$(date)
	if ping -c 3 8.8.8.8 &> /dev/null
	then
		NETWORK_FAIL_COUNT=0
		echo "Internet network ok!"
	else
		NETWORK_FAIL_COUNT=$((NETWORK_FAIL_COUNT+1))
		if [[ $NETWORK_FAIL_COUNT -gt $NETWORK_FAIL_MAX_COUNT ]]
		then
			echo "Need Reboot"
			echo "Need Reboot!@"$(date) >> /home/root/check_eth_dongle.txt
		fi
		if [ -e /sys/class/net/enp1s0u1u4 ]
		then
			echo "got enp1s0u1u4 when Internet network fail!"
			ifconfig enp1s0u1u4 down
		elif [-e /sys/class/net/enp1s0u1u1 ]
		then
			echo "got enp1s0u1u1 when Internet network fail!"
			ifconfig enp1s0u1u1u4 down
		elif [-e /sys/class/net/enp1s0u1u1u4 ]
		then
			echo "got enp1s0u1u1u4 when Internet network fail!"
			ifconfig enp1s0u1u1u4 down
		fi
		echo 0 > sudo tee /sys/bus/usb/devices/1-1/authorized
		echo "before usb power cycle"
		ifconfig
		uhubctl -l 1-1 -a 0 -r 500
		sleep 5
		#uhubctl -l 1-1 -a 1
		sleep 2
		echo "after usb power cycle"
		ifconfig
	fi
	echo "NETWORK_FAIL_COUNT:"$NETWORK_FAIL_COUTN
	sleep 5
done
