#!/bin/sh

APP_URL=$1

setup_enp1_nm.sh
sleep 2

pkill -f cms_check_ext_eth.sh
sleep 1
cms_check_ext_eth.sh &


sleep 1
# pkill -f kill_server_by_time.sh
sync
# kill_server_by_time.sh &

xdotool mousemove 1280 720

echo $APP_URL
sudo chromium --test-type --no-sandbox --force-dark-mode --enable-gpu-rasterization --disable-pings --enable-remote-extensions --force-renderer-accessibility --disable-quic --enable-tcp-fast-open --enable-features=VaapiVideoDecoder --enable-accelerated-video-decode --ignore-gpu-blacklist --autoplay-policy=no-user-gesture-required --window-size=640,480 --window-position=10,10 --app=$APP_URL
