#!/bin/sh
echo "rebuild liblinux_ipc_sem_pyapi"
echo '$0:'$0
echo '$1:'$1
gcc -c -fPIC -o linux_ipc_sem.o linux_ipc_sem.c
gcc -Wl,-rpath=/../ -shared -o liblinux_ipc_sem_pyapi.so linux_ipc_sem.o -lpthread
sync
echo "test"
cp liblinux_ipc_sem_pyapi.so ../
# echo $1 | sudo -S ln -s $PWD/liblinux_ipc_sem_pyapi.so /usr/lib/liblinux_ipc_sem_pyapi.so

