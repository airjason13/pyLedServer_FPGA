#ifndef FS_INOTIFY_H_
#define FS_INOTIFY_H_

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/types.h>
#include <linux/inotify.h>
//#include <fcntl.h>
#include <stdbool.h>
#include <pthread.h>
#include <sys/utsname.h>

void* fs_inotify(void* args);

#endif
