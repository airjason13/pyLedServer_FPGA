#include <sys/shm.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <SDL/SDL.h>
#include <assert.h>
#include <sys/time.h>
#include <signal.h>
#include "linux_ipc_sem.h"
#include <stdbool.h>
#include <time.h>

#define CLOCKID CLOCK_REALTIME

volatile sig_atomic_t flag_exit = 0;
int shm_fd = -1;

#define MAX_WIDTH 1280
#define MAX_HEIGHT 720

#define mask32(BYTE) (*(uint32_t *)(uint8_t [4]){ [BYTE] = 0xff})

#define SHM_SEM_WRITE_URI "/shm_write_sem"
#define SHM_SEM_READ_URI "/shm_read_sem"

int preview_fps = 0;
int frame_id = 0;

static int filter(const SDL_Event * event){
	return event->type == SDL_QUIT;
}

static _Bool init_app(const char *name, SDL_Surface *icon, uint32_t flags){
	printf("init_app start\n");
	atexit(SDL_Quit);
	if(SDL_Init(flags) < 0){
		printf("SDL_Init failed\n");
		return 0;
	}
	SDL_WM_SetCaption(name, name);
	SDL_WM_SetIcon(icon, NULL);
	return 1;
}

static void render(SDL_Surface *sf){
	SDL_Surface *screen = SDL_GetVideoSurface();
	if(SDL_BlitSurface(sf, NULL, screen, NULL) == 0){
		SDL_UpdateRect(screen, 0, 0, 0, 0);
		preview_fps += 1;
	}
}

static uint8_t *init_data(uint8_t *data, int w, int h, int color_channel){
	for(size_t i = w*h*color_channel; i--; ){
		data[i] = (i%3 == 0)?(i/3)%w:(i%3 == 1)?(i/3)/w:0;
	}
	return data;
}

SDL_Surface *init_sdl_window(uint8_t *buf, int w, int h, int cc){
	_Bool ok = init_app("RAW Frame Preview", NULL, SDL_INIT_VIDEO | SDL_INIT_NOPARACHUTE) && 
		SDL_SetVideoMode(w, h, 24, SDL_HWSURFACE | SDL_NOFRAME);

	assert(ok);
	SDL_Surface *data_sf = SDL_CreateRGBSurfaceFrom(
			init_data(buf, w, h, cc), w, h, 24, w*cc,
		       	mask32(0), mask32(1), mask32(2), 0);
	SDL_SetEventFilter(filter);

	return data_sf;
}

void get_sigterm(int signum){
	printf("get_sigterm!\n");
	flag_exit = 1;
}

void fps_counter(void){
	printf("fps : %d\n", preview_fps);
	preview_fps = 0;
}

timer_t jset_timer(timer_t start_sec, long start_nsec, timer_t interval_sec, long interval_nsec, void *func, int sival){
	timer_t timerid;
	struct sigevent evp;
	memset(&evp, 0, sizeof(struct sigevent));
	evp.sigev_value.sival_int = sival;
	evp.sigev_notify = SIGEV_THREAD;
	evp.sigev_notify_function = func;
	if(timer_create(CLOCKID, &evp, &timerid) == -1){
		perror("fail to timer_create");
		return -1;
	}

	struct itimerspec it;
	it.it_interval.tv_sec = interval_sec;
	it.it_interval.tv_nsec = interval_nsec;
	it.it_value.tv_sec = start_sec;
	it.it_value.tv_nsec = start_nsec;
	if(timer_settime(timerid, 0, &it, NULL) == -1){
		perror("fail to timer_settime");
		return -1;
	}
	return timerid;
}

/*******************************************************************
 * Function Name : main
 * Usage : show_ffmpeg_shared_memory src_frame_width src_frame_height show_preview_or_not
 *
*******************************************************************/
int main(int argc, char ** argv){
	if(argc != 5){
		printf("Usage : show_ffmpeg_shared_memory eth_if src_frame_width src_frame_height show_preview_or_not\n");
		return -1;
	}

	printf("Start show_ffmpeg_shared_memory agent!\n");
	//int width = MAX_WIDTH, height = MAX_HEIGHT;
	//char buffer[MAX_WIDTH*MAX_HEIGHT*3];
	char *eth_if = argv[1];
	int src_frame_width = atoi(argv[2]);
	int src_frame_height = atoi(argv[3]);
	int show_preview = atoi(argv[4]);
    char chgrp_cmd[256] = {0};
    char chown_cmd[256] = {0};
	printf("src_frame_width = %d\n", src_frame_width);
	printf("src_frame_height = %d\n", src_frame_height);
	printf("show_preview = %d\n", show_preview);
#if 0
	int width = src_frame_width;
	int height = src_frame_height;
	bool need_scale = false;
#else	
	int width = 640, height = 480;
	bool need_scale = false;
	if((src_frame_width > 640) || (src_frame_height > 480)){
		width = src_frame_width / 2;
		height = src_frame_height / 2;
		need_scale = true;
	}
#endif
	printf("pewview width : %d\n", width);
	printf("pewview height : %d\n", height);
	int color_channels = 3; //RGB24
	char buffer[width*height*3];
	SDL_Surface *sdl_sf;
	SDL_Event event;
	struct sigaction action;

    memset(&action, 0, sizeof(action));
	action.sa_handler = get_sigterm;
	sigaction(SIGTERM | SIGKILL | SIGQUIT | SIGABRT, &action, NULL);

	sem_t *sem_write_flag = py_sem_open(SHM_SEM_WRITE_URI, O_CREAT, 0666, 1);
	sem_t *sem_read_flag = py_sem_open(SHM_SEM_READ_URI, O_CREAT, 0666, 0);

	//time profile
	struct timeval start_time;
	struct timeval memcpy_time;
	struct timeval render_time;
	struct timeval current_time;
#if 0
    system("rm /dev/shm/posixsm");
    system("sync");
    shm_fd = shm_open("posixsm", O_CREAT | O_RDWR, 0777);
    system("sync");
    system("ls -al /dev/shm/posixsm");

    sprintf(chgrp_cmd, "chgrp %s /dev/shm/posixsm", argv[1]);
    printf("chgrp_cmd : %s\n", chgrp_cmd);
    //system("chgrp venom /dev/shm/posixsm");
    system(chgrp_cmd);
    sprintf(chown_cmd, "chown %s /dev/shm/posixsm", argv[1]);
    printf("chown_cmd : %s\n", chown_cmd);
    //system("chown venom /dev/shm/posixsm");
    system(chown_cmd);
    system("chmod 666 /dev/shm/posixsm");

#endif
    system("pulseaudio -D");

	shm_fd = shm_open("posixsm", O_CREAT | O_RDWR, 0666);
	//shm_fd = shm_open("posixsm", O_CREAT | O_RDWR, S_IRUSR | S_IWUSR | S_IXUSR);
	if(shm_fd < 0){
		printf("shared memory open failed!\n");
		return -1;
	}

	ftruncate(shm_fd, 0x400000);
	char *p = mmap(NULL, 0x400000, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
	if(p == NULL){
		printf("mmap failed!\n");
		return -1;
	}
	
	memset(p, 'A', 0x400000);
	
	if(show_preview > 0){
		// init sdl
		sdl_sf = init_sdl_window(buffer, width, height, 3);
		//fps counter timer 
		//timer_t fps_counter_tid = jset_timer(1, 0, 1, 0, &(fps_counter), 99);
	
	}

	// Initial raw socket
	if(set_raw_socket_init(eth_if)){
		printf("socket open failed!\n");
		return -1;
	}	

	py_sem_post(sem_write_flag);

	while(!flag_exit){
		int sem_read_ret = py_sem_timedwait(sem_read_flag, 0, 3);
		//int sem_read_ret = py_sem_trywait(sem_read_flag);
		//printf("sem_read_ret = %d\n", sem_read_ret);
		if(sem_read_ret == -1){
			//printf("sem_read_ret = %d\n", sem_read_ret);
			//gettimeofday(&current_time, NULL);
			//printf("r micro sec : %ld, usec : %ld\n", current_time.tv_sec,  current_time.tv_usec);
			usleep(1);
			continue;
		}
		//printf("sem_read_ret = %d\n", sem_read_ret);
		//gettimeofday(&start_time, NULL);
		// send packet
		frame_id += 1;
		if(frame_id >= 0xffff){
			frame_id = 0;
		}
		//memcpy(buffer, p, src_frame_width*src_frame_height*3);
		//send_rgb_frame_with_raw_socket(buffer, width*height*3, frame_id);
		send_rgb_frame_with_raw_socket(p, width*height*3, frame_id);
		
		//gettimeofday(&memcpy_time, NULL);

		if(show_preview > 0){
			//gettimeofday(&start_time, NULL);
			if(need_scale == true){
					for(int y = 0; y < height; y ++){
						for(int x = 0; x < width; x++){
							memcpy(&buffer[3*(y*width + x)], &p[3*((4*y*width) + (2*x))], 3);
						}
					}
			}else{
				memcpy(buffer, p, src_frame_width*src_frame_height*3);
			}
		}
		//
		py_sem_post(sem_write_flag);
		//gettimeofday(&memcpy_time, NULL);
		if(show_preview > 0){
			//printf("render!\n");
			render(sdl_sf);
		}
		//gettimeofday(&render_time, NULL);
		//printf("s micro sec : %ld\n", start_time.tv_usec);
		//printf("m micro sec : %ld\n", memcpy_time.tv_usec);
		//printf("r micro sec : %ld\n", render_time.tv_usec);
		//usleep(1000);
	}
    printf("ready to quit!\n");
	py_sem_close(sem_write_flag);
	py_sem_unlink(SHM_SEM_WRITE_URI);
	py_sem_close(sem_read_flag);
	py_sem_unlink(SHM_SEM_READ_URI);

	munmap(p, 0x400000);
	unlink(shm_fd);

	return 0;

}
