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


while :
do
	get_dns_list

	echo ${dns[*]}

	dns_list_len=${#dns[@]}

	echo dns_list_len:$dns_list_len


	#for i in $( seq 0 $dns_list_len )
	for (( i = 0; i < $dns_list_len; i++ ))
	do 
		echo dns[$i]:${dns[$i]}
		if ping -c 3 ${dns[$i]} &> /dev/null
		then
			echo ping ${dns[$i]} ok
		else
			echo ping ${dns[$i]} ng	
		fi
	done

	
done



