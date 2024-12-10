#ifndef SHOW_FFMPEG_SHARED_MEMORY_H_
#define SHOW_FFMPEG_SHARED_MEMORY_H_

#include <sys/shm.h>
#include <sys/mman.h>
#include <unistd.h>
//#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#ifdef ENABLE_SDL
#include <SDL/SDL.h>
#endif
#include <assert.h>
#include <sys/time.h>
#include <signal.h>
#include <stdbool.h>
#include <time.h>
#include <sys/utsname.h>
#include <omp.h>

#include "linux_ipc_sem.h"
#include "raw_socket.h"
#include "fs_inotify.h"
#include "utildbg.h"

#endif