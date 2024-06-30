#ifndef _UTILDBG_H_
#define _UTILDBG_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <stdarg.h>
#include <errno.h>
#include <stdbool.h>
#include <time.h>
#include <pthread.h>
#define LOG_VERSION "0.1.0"

/*+++++++++++++++++++++++ori temp debug marco++++++++++++++++++++*/
/*#define _DEBUG

#ifdef DEBUG
#define DEBUG(format, args...) printf("[%s:%d] "format, __FILE__, __LINE__, ##args)
#else
#define DEBUG(args...) do{}while(0)
#endif*/
/*-----------------------ori temp debug marco----------------------*/

#define LOG_FILE_PATH 		"./ffmpeg_shared_memory_log/"
#define LOG_CONFIG_FILE		".log_config"
//for log file prefix
//LOG_PREFIX_TIME : ex. 20210723_141516.log
//LOG_PREFIX_ID   : ex. 0001.log 
#define LOG_PREFIX_TIME		0
#define LOG_PREFIX_ID		1

#define LOG_FILE_MAX_SIZE	65535
#define LOG_USE_COLOR
/*static const char *level_names[] = {
    "TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"
};*/

#define MAX_TAG_NUM     64
#define LEVEL_STRLENGTH 32
#define stringiz(arg)   #arg



typedef enum
{
    e_TRACE = 0,
    e_DEBUG,
    e_INFO,
    e_WARN,
    e_ERROR,
    e_FATAL
} log_level_name;

#define LOG_LEVEL_MAX   FATAL

/*char j_log_level[5][LEVEL_STRLENGTH] = {
    stringiz(TRACE),
    stringiz(DEBUG),
    stringiz(INFO),
    stringiz(WARN),
    stringiz(ERROR),
    stringiz(FATAL),
};*/

typedef void (*log_LockFn)(void *udata, int lock);

enum { LOG_TRACE, LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR, LOG_FATAL };

void jlog(int level, const char *file, int line, const char *fmt, ...);

#define log_trace(...)  jlog(LOG_TRACE, __FILE__, __LINE__, __VA_ARGS__)
#define log_debug(...)  jlog(LOG_DEBUG, __FILE__, __LINE__, __VA_ARGS__)
#define log_info(...)   jlog(LOG_INFO,  __FILE__, __LINE__, __VA_ARGS__)
#define log_warn(...)   jlog(LOG_WARN,  __FILE__, __LINE__, __VA_ARGS__)
#define log_error(...)  jlog(LOG_ERROR, __FILE__, __LINE__, __VA_ARGS__)
#define log_fatal(...)  jlog(LOG_FATAL, __FILE__, __LINE__, __VA_ARGS__)

void log_set_udata(void *udata);
void log_set_lock(log_LockFn fn);
void log_set_fp(FILE *fp);
void log_set_level(int level);
void log_set_quiet(int enable);
int renew_log_file(int type);
int log_init(bool log_file_enable, int type);
void dump_memory_data(unsigned char *buf, int size);
char* popen_cmd(char *cmd);
bool detect_screen(void);
//void jlog(int level, const char *file, int line, const char *fmt, ...);



#ifdef __cplusplus
}
#endif

#endif  //_UTILDBGMSG_H_
