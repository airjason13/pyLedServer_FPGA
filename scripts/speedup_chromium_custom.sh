#!/bin/sh

echo "Moving write-busy temp files to tmpfs /dev/shm..."
mkdir -p /dev/shm/chromium

echo "   ~/.config/chromium/Default/Service Worker/"
mkdir -p /dev/shm/chromium/serviceWorker
rm -rf "$HOME/.config/chromium/Default/Service Worker"
ln -s /dev/shm/chromium/serviceWorker/ "$HOME/.config/chromium/Default/Service Worker"

echo "   ~/.cache/chromium/"
mkdir -p /dev/shm/chromium/cache
rm -rf $HOME/.cache/chromium
ln -s /dev/shm/chromium/cache/ $HOME/.cache/chromium

echo "Starting chromium..."
OS=$(uname -m)
if [ $OS == "armv7l" ]
then
   echo "   32-bit with Linux aarch64 user agent"
   chromium-browser --user-agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
elif [ $OS == "aarch64" ]
then
   echo "   64-bit"
   #chromium
   chromium_custom.sh $1 &
else
   echo "Unrecognized pi os type: $OS"
fi

echo "Cleaning up /dev/shm ..."
rm -rf /dev/shm/chromium
rm -rf "$HOME/.config/chromium/Default/Service Worker"
rm -rf $HOME/.cache/chromium
