#!/bin/sh
read MAC < /sys/class/net/eth0/address
echo $MAC
REG_MAC=$(echo $MAC | sed 's/://g')  
echo $REG_MAC
STRING_TO_ENCODE='mac_id='$REG_MAC'|at_reg&s=foxconngis_site01'
echo $STRING_TO_ENCODE
URL_EXTEND=$(echo -n $STRING_TO_ENCODE | base64)
echo $URL_EXTEND
APP_URL=https://icast.tw/icast/educ/#$URL_EXTEND

cms_check_ext_eth.sh &

sleep 1
pkill -f kill_server_by_time.sh
sync
kill_server_by_time.sh &

xdotool mousemove 1280 720

echo $APP_URL
sudo chromium --test-type --no-sandbox --force-dark-mode --enable-gpu-rasterization --disable-pings --enable-remote-extensions --force-renderer-accessibility --disable-quic --enable-tcp-fast-open --enable-features=VaapiVideoDecoder --enable-accelerated-video-decode --ignore-gpu-blacklist --autoplay-policy=no-user-gesture-required --window-size=640,480 --window-position=10,10 --app=$APP_URL
