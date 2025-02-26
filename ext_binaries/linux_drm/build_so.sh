#!/bin/sh
echo "rebuild linux_libdrm"
echo '$0:'$0
echo '$1:'$1
gcc -shared -o linux_libdrm.so -fPIC libdrm.c $(pkg-config --cflags --libs libdrm)
sync
echo "test"
cp linux_libdrm.so ../


