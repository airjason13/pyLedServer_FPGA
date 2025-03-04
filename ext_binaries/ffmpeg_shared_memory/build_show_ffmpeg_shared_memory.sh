#!/bin/sh
echo '$0:'$0
echo '$1:'$1

ENABLE_SDL=${1:-0}
CFLAGS="-O2 -Wall -fopenmp"
LDFLAGS=""

if [ "$ENABLE_SDL" = "1" ]; then
    CFLAGS="$CFLAGS -DENABLE_SDL"
    LDFLAGS="$LDFLAGS $(pkg-config --cflags --libs sdl)"
fi

gcc $CFLAGS show_ffmpeg_shared_memory.c raw_socket.c fs_inotify.c utildbg.c \
    -L../linux_ipc_sem -llinux_ipc_sem_pyapi -o show_ffmpeg_shared_memory $LDFLAGS

# Set network capabilities using setcap to allow raw socket usage
echo $1 | sudo -S setcap cap_net_raw+ep show_ffmpeg_shared_memory
if [ $? -ne 0 ]; then
    echo "setcap failed, using chmod u+s instead"
    sudo chmod u+s show_ffmpeg_shared_memory
fi

# Copy the compiled binary to the parent directory
cp show_ffmpeg_shared_memory ../

# Apply setcap again to the copied file
echo $1 | sudo -S setcap cap_net_raw+ep ../show_ffmpeg_shared_memory
if [ $? -ne 0 ]; then
    echo "setcap failed, using chmod u+s instead"
    sudo chmod u+s ../show_ffmpeg_shared_memory
fi
