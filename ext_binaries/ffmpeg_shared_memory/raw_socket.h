#ifndef RAW_SOCKET_H_
#define RAW_SOCKET_H_

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <string.h>
#include <linux/if_packet.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <netinet/ether.h>
#include <pthread.h>
#include <unistd.h>
//#include <fcntl.h>
#include <stdbool.h>
#include "utildbg.h"

#define MAX_FRAME_SIZE 1476 + 14
#define CMD_HEAD_SZ 20
#define MAX_DATA_LENGTH 1500 + 14

#define MACHINE_TYPE_Pi4    0
#define MACHINE_TYPE_Pi5    1
#define MACHINE_TYPE_X86    2


int send_rgb_frame_with_raw_socket(unsigned char *rgb_frame, int frame_sz, unsigned int frame_id, int machine_type);
int set_raw_socket_init(const char *interface);
int set_brightness_value(int value);

#endif