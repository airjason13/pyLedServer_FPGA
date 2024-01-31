#ifndef LINUX_IPC_SEM_H_
#define LINUX_IPC_SEM_H_



#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/time.h>
#include <errno.h>

#include <fcntl.h>	/* O_CRAT */
#include <sys/stat.h>
#include <semaphore.h>

extern void* py_sem_open(const char *__name, int __oflag, unsigned int  mode, unsigned int value);
extern int py_sem_close(void* sem_flag);
extern int py_sem_unlink(const char *__name);
extern int py_sem_wait(void* sem_flag);
extern int py_sem_timedwait(void* sem_flag, long int secs, long int nsecs);
extern int py_sem_trywait(void* sem_flag);
extern int py_sem_post(void* sem_flag);
extern int py_sem_getvalue(void* sem_flag);

#endif /* LINUX_IPC_SEM_H_ */

