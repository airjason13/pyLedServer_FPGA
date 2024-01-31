#!/bin/sh


gcc -c -fPIC -o linux_ipc_sem.o linux_ipc_sem.c
gcc -Wl,-rpath=/../ -shared -o liblinux_ipc_sem_pyapi.so linux_ipc_sem.o -lpthread
cp liblinux_ipc_sem_pyapi.so ../
# ln -s $PWD/liblinux_ipc_sem_pyapi.so /usr/lib/liblinux_ipc_sem_pyapi.so

