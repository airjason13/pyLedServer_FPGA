#!/bin/sh
# This shell script is only for rpi4

# step 0: clean previous nmcli connection
NM_NAME=enp1
nmcli con del enp1

# step 1: find ext eth adapter
EXT_ETH_ADAPTER=""
STATIC_IP=""
GATEWAY=""
DNS=""
while true;do
	str=$(ls /sys/class/net/)
	arr_str=($str)
	for i in "${arr_str[@]}"
	do
		if [[ "$i" =~ ^enp* ]];then
			echo found $i
			EXT_ETH_ADAPTER=$i
		fi
	done
	if [[ "$EXT_ETH_ADAPTER" =~ ^enp* ]];then
		echo EXT_ETH_ADAPTER:$EXT_ETH_ADAPTER
		break
	else
		echo "not found ext eth adapter"
		sleep 5
	fi
done

# step 2: get network infomation
info_file_uri="/home/root/pyLedServer_FPGA/led_config/ext_eth_setting.dat"
while IFS= read -r line
do 
	echo $line
	if [[ "$line" =~ ^static_ip* ]];then
		arr_str=(${line//:/ })
		STATIC_IP=${arr_str[1]}
		echo static_ip: $STATIC_IP
	elif [[ "$line" =~ ^gateway* ]];then
		arr_str=(${line//:/ })
		GATEWAY=${arr_str[1]}
		echo gateway: $GATEWAY
	elif [[ "$line" =~ ^dns* ]];then
		arr_str=(${line//:/ })
		DNS=${arr_str[1]}
		echo gateway: $DNS	
	fi

done < "$info_file_uri"

# step 3: check data 
DATA_OK=true
if [[ "$STATIC_IP" =~ ^x* ]];then
	echo STATIC_IP LEN:${#STATIC_IP}
	DATA_OK=false
fi
if [[ "$GATEWAY" =~ ^x* ]];then
	echo GATEWAY LEN:${#GATEWAY}
	DATA_OK=false
fi
if [[ "$DNS" =~ ^x* ]];then
	echo STATIC_IP LEN:${#DNS}
	DATA_OK=false
fi

# DATA_OK=false
if [[ $DATA_OK =~ false ]];then
	echo DATA_OK:$DATA_OK
	# let it go with dhcp
	nmcli con add type ethernet ifname $EXT_ETH_ADAPTER con-name $NM_NAME
	nmcli con mod $NM_NAME ipv4.method auto

	nmcli con up $NM_NAME
	exit	
fi

pkill -f ffmpeg

route del default 
sleep 2

# nmcli con del enp1s0u1u3
nmcli con add type ethernet ifname $EXT_ETH_ADAPTER con-name $NM_NAME
nmcli con mod $NM_NAME ipv4.addresses $STATIC_IP
nmcli con mod $NM_NAME ipv4.gateway $GATEWAY
nmcli con mod $NM_NAME ipv4.dns "$DNS"
nmcli con mod $NM_NAME ipv4.method manual
nmcli con up $NM_NAME
