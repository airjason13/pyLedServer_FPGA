#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <sys/stat.h>
#include "utildbg.h"

static struct
{
    void *udata;
    log_LockFn lock;
    FILE *fp;
    int level;
    int quiet;
	char fname[256];
	int log_file_prefix_type;
	pthread_t tid;
	pthread_mutex_t mutex_lock;
} L;


static const char *level_names[] =
{
    "TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"
};

#ifdef LOG_USE_COLOR
static const char *level_colors[] =
{
    "\x1b[94m", "\x1b[36m", "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[35m"
};
#endif

void check_log_file(void){
	struct stat st;

	while(1){
		pthread_mutex_lock(&L.mutex_lock);
		stat(L.fname, &st);
		long size = st.st_size;
		//printf("size = %ld\n", size);
		
		if(size > LOG_FILE_MAX_SIZE){
			renew_log_file(L.log_file_prefix_type);
			//printf("fname = %s\n", L.fname);
			//printf("fp = %x\n", L.fp);
		}
		pthread_mutex_unlock(&L.mutex_lock);
		usleep(3000);
	}
}


char ignore_tag[MAX_TAG_NUM][32] = {""};
char show_tag[MAX_TAG_NUM][32] = {""};

int parser_ignore_tag(char *log_tag_str){
    int i = 0;
    int res = 0;

    for(i = 0; i < MAX_TAG_NUM; i++)
    {
        if(!strcmp(ignore_tag[i], ""))
        {
            strcpy(ignore_tag[i], log_tag_str);
            printf("ignore_tag[%d] = %s\n", i, ignore_tag[i]);
            res = 0;
            return res;
        }
    }

    printf("ignore_tag buffer overflow!\n");
    res = -ENOMEM;
    return res;
}

int parser_show_tag(char *log_tag_str)
{
    int i = 0;
    int res = 0;

    for(i = 0; i < MAX_TAG_NUM; i++)
    {
        if(!strcmp(show_tag[i], ""))
        {
            strcpy(show_tag[i], log_tag_str);
            printf("show_tag[%d] = %s\n", i, show_tag[i]);
            res = 0;
            return res;
        }
    }

    printf("show_tag buffer overflow!\n");
    res = -ENOMEM;
    return res;
}



int parser_log_level(char *log_level_str)
{
    int i;
    char l_str[LEVEL_STRLENGTH];
    int l_level = 0;

    for(i = e_TRACE; i <= e_FATAL; i ++)
    {
        switch(i)
        {
            case e_WARN:
                strcpy(l_str, stringiz(WARN));
                l_level = i;
                break;

            case e_TRACE:
                strcpy(l_str, stringiz(TRACE));
                l_level = i;
                break;

            case e_INFO:
                strcpy(l_str, stringiz(INFO));
                l_level = i;
                break;

            case e_DEBUG:
                strcpy(l_str, stringiz(DEBUG));
                l_level = i;
                break;

            case e_ERROR:
                strcpy(l_str, stringiz(ERROR));
                l_level = i;
                break;

            case e_FATAL:
                strcpy(l_str, stringiz(FATAL));
                l_level = i;
                break;

            default:
                printf("got debug level unknow!\n");
                break;
        }

        if(!strcasecmp(l_str, log_level_str))
        {
            printf("got l_str = %s, l_level = %d\n", l_str, l_level);
            log_set_level(l_level);
            return 0;
        }
    }

    printf("the debug level unknow!\n");
    return -EINVAL;
}

/*parameter :
*               tag_str : the log_xxxx tag parameter
* return    :
*               0               : ok to show this tag
*               nonzero value   : do not show this tag log
*/
static int check_tag(char *tag_str)
{
    int ret = 0;
    int i = 0;
    int j = 0;
    bool got_ignore_all = false;

    for(i = 0; i < MAX_TAG_NUM; i ++)
    {
        if(!strcmp(ignore_tag[i], ""))
        {
            return 0;
        }

        if(!strcasecmp(ignore_tag[i], "all"))
        {
            got_ignore_all = true;

            for(j = 0; j < MAX_TAG_NUM; j++)
            {
                if(!strcasecmp(show_tag[j], ""))
                {
                    if(j == 0)
                    {
                        if(!L.quiet)
                        {
                            log_set_quiet(1);
                        }

                        return -1;
                    }

                    //j = MAX_TAG_NUM;
                    return -1;
                }
                else if(!strcmp(show_tag[j], tag_str))
                {
                    return 0;
                }
            }
        }
        else
        {
            if(!strcasecmp(ignore_tag[i], tag_str))
            {
                return -1;
            }
        }
    }

    return 0;
}

static void lock(void)
{
    if(L.lock)
    {
        L.lock(L.udata, 1);
    }
}


static void unlock(void)
{
    if(L.lock)
    {
        L.lock(L.udata, 0);
    }
}


void log_set_udata(void *udata)
{
    L.udata = udata;
}


void log_set_lock(log_LockFn fn)
{
    L.lock = fn;
}


void log_set_fp(FILE *fp)
{
    L.fp = fp;
}


void log_set_level(int level)
{
    L.level = level;
}


void log_set_quiet(int enable)
{
    L.quiet = enable ? 1 : 0;
}


void jlog(int level, const char *file, int line, const char *fmt, ...)
{
	time_t rawtime;
    struct tm 		*tm;
    if(level < L.level){
        printf("Level too high!\n");
        return;
    }

    if(L.quiet){
        printf("LOG QUIET!\n");
        return;
    }

    /*check the tag ignore and show*/
    if(check_tag(file)){
        printf("Do not show this message!\n");
        return;
    }
    /* Acquire lock */
    lock();

    /* Get current time */
	(void) time(&rawtime);
	tm = localtime(&rawtime);
    /* Log to stderr */
    if(!L.quiet){
        va_list args;
        //char buf[16];
        char buf[128];
		
        buf[strftime(buf, sizeof(buf), "%H:%M:%S", tm)] = '\0';
#ifdef LOG_USE_COLOR
        fprintf(
            stderr, "%s %s%-5s\x1b[0m \x1b[90m%s:%d:\x1b[0m ",
            buf, level_colors[level], level_names[level], file, line);
#else
        fprintf(stderr, "%s %-5s %s:%d: ", buf, level_names[level], file, line);
#endif
        va_start(args, fmt);
        vfprintf(stderr, fmt, args);
        va_end(args);
        fprintf(stderr, "\n");
        fflush(stderr);
    }
    /* Log to file */
    if(L.fp){
        va_list args;
        char buf[32];
        buf[strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", tm)] = '\0';
        fprintf(L.fp, "%s %-5s %s:%d: ", buf, level_names[level], file, line);
        va_start(args, fmt);
        vfprintf(L.fp, fmt, args);
        va_end(args);
        fprintf(L.fp, "\n");
        fflush(L.fp);
    }

    /* Release lock */
    unlock();
}

//static 
void lock_callback(void *udata, int lock){
	if(lock){
		pthread_mutex_lock(udata);	
	}else{
		pthread_mutex_unlock(udata);	
	}
}

int renew_log_file(int type){
	FILE *tmpfp = NULL;
	time_t rawtime;
    struct tm 		*tm;
	char filename[256] = {0};
	char buf[64];
	int err;

	//close original log_file handler first
	fclose(L.fp);
	L.fp = NULL;

	if(type == LOG_PREFIX_TIME){	
		(void) time(&rawtime);
		tm = localtime(&rawtime);
    	buf[strftime(buf, sizeof(buf), "%Y%m%d_%H%M%S", tm)] = '\0';
		sprintf(filename, "%ssfsm_%s.log", LOG_FILE_PATH, buf);
	}else if(type == LOG_PREFIX_ID){
		char config_fname[256] = {0};
		sprintf(config_fname, "%s%s", LOG_FILE_PATH, LOG_CONFIG_FILE);
		FILE* config_file = fopen(config_fname, "r");
		unsigned int tmp_id = 0;
		if(config_file == NULL){
			//new a config_file
			config_file = fopen(config_fname, "w+");
			fprintf(config_file, "log_file_id:1\n");
			fsync(config_file);
			fclose(config_file);
			config_file = fopen(config_fname, "r");

		}
		fscanf(config_file, "log_file_id:%d\n", &tmp_id);
		printf("tmp_id : %d\n", tmp_id);
		sprintf(filename, "%ssfsm_%04d.log", LOG_FILE_PATH, tmp_id);
		printf("log filename : %s\n", filename);
		//remove first
		remove(filename);
		//re-write new id to config
		fclose(config_file);
		remove(config_fname);
		config_file = fopen(config_fname, "w+");
		if(config_file == NULL){
			printf("config file re-write error!\n");
			return -1;
		}else{
			if(tmp_id >= 6){
				tmp_id = 1;
			}else{
				tmp_id ++;
			}
			printf("re-write log config file to %d id!\n", tmp_id);
			fprintf(config_file, "log_file_id:%d\n", tmp_id);
			fsync(config_file);
			fclose(config_file);
		}
	}else{
		printf("Log TYPE ERROR!\n");
	}
	
	tmpfp = fopen(filename, "w");
	if(tmpfp != NULL){
		L.fp = tmpfp;
		strcpy(L.fname, filename);
		return 0;
	}
		
	return -1;
}

/*****************************************
* function 	: int log_init(bool enable, int type)
* param		: bool enable => enable log to file or not
*			  int type => file name prefix type  
* return 	: 0  => success
*			  -1 => fail
******************************************/
int log_init(bool enable, int type){
	FILE *tmpfp = NULL;
	time_t rawtime;
    struct tm 		*tm;
	char filename[256] = {0};
	char buf[64];
	int err;

	if (pthread_mutex_init(&(L.mutex_lock), NULL) != 0){
        printf("\n mutex init failed\n");
        return 1;
    }else{
		log_set_udata(&L.mutex_lock);
		log_set_lock(&lock_callback);
	}

	if(enable == false){
		return 0;
	}

	if(access(LOG_FILE_PATH, 0)==-1){
        if (mkdir(LOG_FILE_PATH, 0777)){
            printf("creat file bag failed!!!");
        }
    }
	
	if(type == LOG_PREFIX_TIME){	
		(void) time(&rawtime);
		tm = localtime(&rawtime);
    	buf[strftime(buf, sizeof(buf), "%Y%m%d_%H%M%S", tm)] = '\0';
		sprintf(filename, "%sfsm_%s.log", LOG_FILE_PATH, buf);
	}else if(type == LOG_PREFIX_ID){
		char config_fname[256] = {0};
		sprintf(config_fname, "%s%s", LOG_FILE_PATH, LOG_CONFIG_FILE);
		FILE* config_file = fopen(config_fname, "r");
		int tmp_id = 0;
		if(config_file == NULL){
			//new a config_file
			config_file = fopen(config_fname, "w+");
			fprintf(config_file, "log_file_id:1\n");
			fsync(config_file);
			fclose(config_file);
			config_file = fopen(config_fname, "r");
			//return -1;
		}
		fscanf(config_file, "log_file_id:%d\n", &tmp_id);
		printf("tmp_id : %d\n", tmp_id);
		sprintf(filename, "%ssfsm_%04d.log", LOG_FILE_PATH, tmp_id);
		printf("log filename : %s\n", filename);
		//re-write new id to config
		fclose(config_file);
		remove(config_fname);
		printf("remove ok!\n");
		config_file = fopen(config_fname, "w+");
		if(config_file == NULL){
			printf("config file re-write error!\n");
			return -1;
		}else{
			if(tmp_id >= 6){
				tmp_id = 1;
			}else{
				tmp_id ++;
			}
			printf("re-write log config file!\n");
			fprintf(config_file, "log_file_id:%d\n", tmp_id);
			printf("re-write ok!\n");
			fsync(config_file);
			fclose(config_file);
		}

	}else{
		printf("Log TYPE ERROR!\n");
	}
	
	L.log_file_prefix_type = type;

	tmpfp = fopen(filename, "w");
	if(tmpfp != NULL){
		L.fp = tmpfp;
		strcpy(L.fname, filename);
		err = pthread_create(&(L.tid), NULL, &check_log_file, NULL);
        if (err != 0){
            printf("\ncan't create thread :[%s]", strerror(err));
			return -1;
		}
		return 0;
	}
	L.fp = NULL;//disable log to file
	return -1;
	
}

void dump_memory_data(unsigned char *buf, int size)
{
	int i = 0;
	for(i = 0; i < size; i++){
		if((i%10) == 0)
			printf("\n");
		printf("0x%x ", buf[i]);
	}
	printf("\n");
	
}

char* popen_cmd(char *cmd)
{
    FILE *fp;
    char buf[256];
    fp = popen(cmd, "r");
    fgets(buf, sizeof(buf), fp);
    printf("%s", buf);
    pclose(fp);    
    return buf;
}

bool detect_screen(void)
{
    FILE *fp;
    char buf[256];
    bool bret = false;
    char *cmd = "xrandr";
    fp = popen(cmd, "r");
    while(true){
        if(NULL == fgets(buf, sizeof(buf), fp)){
            break;
        }
        if(strstr(buf, "HDMI-1 connected") 
            || (strstr(buf, "HDMI-2 connected"))){
            bret = true;
            break;
        } 
    }
    pclose(fp);    
    return bret;
}
