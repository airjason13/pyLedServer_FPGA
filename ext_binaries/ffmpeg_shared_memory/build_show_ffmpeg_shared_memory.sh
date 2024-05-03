#!/bin/sh
echo '$0:'$0
echo '$1:'$1

gcc -fopenmp show_ffmpeg_shared_memory.c raw_socket.c fs_inotify.c $(pkg-config --cflags --libs sdl) -L../linux_ipc_sem \
    -llinux_ipc_sem_pyapi -o show_ffmpeg_shared_memory

echo $1 | sudo -S setcap cap_net_raw+ep show_ffmpeg_shared_memory
cp show_ffmpeg_shared_memory ../

echo $1 | sudo -S setcap cap_net_raw+ep ../show_ffmpeg_shared_memory
