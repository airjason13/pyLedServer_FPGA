#!/bin/sh


function get_dns_list() {
	dns=()
	resolv_file_uri="/etc/resolv.conf"
	while IFS= read -r line
	do
		# echo $line
		if [[ "$line" =~ ^nameserver* ]];then
			arr_str=(${line//:/ })
			nameserver=${arr_str[1]}
			# echo nameserver:$nameserver
			dns+=($nameserver)
		fi
	done < "$resolv_file_uri"

	echo ${dns[*]}
	
	# return ${dns[*]}
}


function get_ext_eth_interface() {
	_EXT_ETH_ADAPTER=""
	str=$(ls /sys/class/net/)
	arr_str=($str)
	for i in "${arr_str[@]}"
	do 
		if [[ "$i" =~ ^enp* ]];then
			_EXT_ETH_ADAPTER=$i
		fi
	done
	if [[ "$_EXT_ETH_ADAPTER" =~ ^enp* ]];then
		echo $_EXT_ETH_ADAPTER
	else
		echo "NONE"
	fi	
}

#get_ext_eth_interface
#echo $_EXT_ETH_ADAPTER

function get_ext_eth_dns() {
	info_file_uri="/home/root/pyLedServer_FPGA/led_config/ext_eth_setting.dat"
	while IFS= read -r line
	do
		if [[ "$line" =~ ^dns* ]];then
			arr_str=(${line//:/ })
			DNS=${arr_str[1]}
		fi
	done < "$info_file_uri"
	echo $DNS
}

function get_ext_eth_dns_by_nmcli() {
  DNS_STR=$(nmcli device show $_EXT_ETH_ADAPTER | grep "DNS")
  arr_str=(${DNS_STR//:/ })
  DNS=${arr_str[1]}
  echo $DNS
}

EXT_ETH_FAIL_COUNT_LOG_FILE_URI="/home/root/ext_eth_fail.log"
NETWORK_FAIL_COUNT=0


while :
do
	get_ext_eth_interface
	echo $_EXT_ETH_ADAPTER
	if [[ "$_EXT_ETH_ADAPTER" =~ ^NONE* ]]; then
	  echo "Missing enp ready to power cycle USB port"
		uhubctl -l 1-1 -a 0
		sleep 5
		uhubctl -l 1-1 -a 1
		sleep 2
		echo 0 > /sys/bus/usb/devices/1-1/authorized
    sleep 2
    echo 1 > /sys/bus/usb/devices/1-1/authorized

		# setup_enp1_nm.sh &
		pkill -f main.py
		sleep 2
	  continue
	fi
	# get_ext_eth_dns
	get_ext_eth_dns_by_nmcli
	echo $DNS

	if ping -I $_EXT_ETH_ADAPTER -c 3 $DNS&> /dev/null
	then
		NETWORK_FAIL_COUNT=0
		echo "Internet network ok"
	else
		NETWORK_FAIL_COUNT=$((NETWORK_FAIL_COUNT+1))
		echo "EXT_ETH_FAIL_COUNT:"$NETWORK_FAIL_COUNT: $(date) >> $EXT_ETH_FAIL_COUNT_LOG_FILE_URI
		
		echo 0 > sudo tee /sys/us/usb/devices/1-1/authorized
		echo "Cannot Ping DNS ready to power cycle USB port"
		uhubctl -l 1-1 -a 0 
		sleep 5
		uhubctl -l 1-1 -a 1 
		sleep 2
		echo 0 > /sys/bus/usb/devices/1-1/authorized
    sleep 2
    echo 1 > /sys/bus/usb/devices/1-1/authorized

		# setup_enp1_nm.sh &
		pkill -f main.py
		sleep 2
	fi
	sleep 30
done



