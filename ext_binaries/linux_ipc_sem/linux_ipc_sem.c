#include "linux_ipc_sem.h"

void* py_sem_open(const char *__name, int __oflag, unsigned int mode, unsigned int value)
{
	sem_t* sem_flag = NULL;

	sem_flag = sem_open(__name, __oflag, (mode_t)mode, value);

	if (NULL == sem_flag)
	{
		fprintf(stderr, "failed to open semaphore: %s\n", __name);
		return NULL;
	}

	return (void*)sem_flag;
}


int py_sem_close(void* sem_flag)
{
	int ret_flag = -1;

	ret_flag = sem_close((sem_t*)sem_flag);

	return ret_flag;
}


int py_sem_unlink(const char *__name)
{
	int ret_flag = -1;
	ret_flag = sem_unlink(__name);

	return ret_flag;
}

int py_sem_wait(void* sem_flag)
{
	int ret_flag = -1;
	ret_flag = sem_wait((sem_t*)sem_flag);

	return ret_flag;
}

int py_sem_timedwait(void* sem_flag, long int secs, long int nsecs)
{
	int ret_flag = -1;
	struct timespec delay_time = {0};
	delay_time.tv_sec = secs;
	delay_time.tv_nsec = nsecs;

	ret_flag = sem_timedwait((sem_t*)sem_flag, &delay_time);

	return ret_flag;
}

int py_sem_trywait(void* sem_flag)
{
	int ret_flag = -1;

	ret_flag = sem_trywait((sem_t*)sem_flag);

	return ret_flag;
}

int py_sem_post(void* sem_flag)
{
	int ret_flag = -1;

	ret_flag = sem_post((sem_t*)sem_flag);

	return ret_flag;
}

int py_sem_getvalue(void* sem_flag)
{
	int ret_flag = -1;
	int val_addr = -1;

	ret_flag = sem_getvalue((sem_t*)sem_flag, &val_addr);
	if(ret_flag < 0)
	{
		fprintf(stderr, "failed to get sem val\n");
	}

	return val_addr;
}
