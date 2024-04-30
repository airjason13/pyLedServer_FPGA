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
#include <fcntl.h>
#include <stdbool.h>

#define MAX_FRAME_SIZE 1476
//#define MAX_FRAME_SIZE 1024
#define CMD_HEAD_SZ 20
#define MAX_DATA_LENGTH 1500

int raw_sock = -1;
unsigned short int packet_index = 0;
struct sockaddr_ll socket_address;
struct ifreq ifr;

int set_raw_socket_init(const char *interface)
{
    int ss = 0;
    struct sockaddr_ll sa;
    size_t if_name_len = 0;

    if_name_len = strlen(interface);

    if (raw_sock != -1)
        close(raw_sock);

    raw_sock = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

    if (raw_sock < 0) {
        fprintf(stderr, "Error: Can't open socket.\n");
        return -1;
    }

    if (if_name_len < sizeof(ifr.ifr_name)) {
        memcpy(ifr.ifr_name, interface, if_name_len);
        ifr.ifr_name[if_name_len] = 0;
    } else {
        close(raw_sock);
        return -1;
    }

    ioctl(raw_sock, SIOCGIFINDEX, &ifr);

    memset(&sa, 0, sizeof(sa));
    sa.sll_family = PF_PACKET;
    sa.sll_protocol = 0x0000;
    sa.sll_ifindex = ifr.ifr_ifindex;
    sa.sll_hatype = 0;
    sa.sll_pkttype = PACKET_HOST;

    bind(raw_sock, (const struct sockaddr *)&sa, sizeof(sa));
    ss = setsockopt(raw_sock, SOL_SOCKET, SO_BINDTODEVICE, interface, strlen(interface));

    /* Venom test*/
    //int flags = fcntl(raw_sock, F_GETFL, 0);
    //fcntl(raw_sock, F_SETFL, flags | SOCK_NONBLOCK);

    if (ss < 0) {
        close(raw_sock);
        return -1;
    }

    return 0;
}

int send_raw_socket_packet(unsigned char *packet_data , int packet_sz)
{
    socket_address.sll_ifindex = ifr.ifr_ifindex;
    socket_address.sll_halen = ETH_ALEN;
    memcpy(socket_address.sll_addr, packet_data + 6, 6);

    int ret = 0;
#if 1
    ret = sendto(raw_sock, packet_data, packet_sz, 0, (struct sockaddr *)&socket_address, sizeof(struct sockaddr_ll));
   if(ret != packet_sz){
   	printf("send error!\n");
   } 
#else
    if (sendto(raw_sock, packet_data, packet_sz, 0, (struct sockaddr *)&socket_address, sizeof(struct sockaddr_ll)) < 0) {
        printf("Send failed\n");
        return -1;
    }
#endif
    return 1;
}

int send_frame_packet(unsigned char *data, unsigned int length,unsigned int offset)
{
    unsigned char combined_data[MAX_DATA_LENGTH];
    unsigned int packet_sz;
    unsigned int length_offset = 4;
    uint8_t brocast_cmd[CMD_HEAD_SZ] = {
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, //Destination Address
        0x00, 0x00, 0x00, 0x00, 0x00, 0x01, //Source Address
        0x00, //Packet Index
        0x00, 0x00, //Number of Data Byte
        0x1E, //Flow Ctrl 
        0x00, 0x00, 0x00, 0x00,//Reg
    };
    unsigned char crc[4] = {0xCC,0xCC,0xCC,0xCC};
    
    packet_sz = length+CMD_HEAD_SZ+4;
	
    if (packet_sz > MAX_DATA_LENGTH) {
        printf("Send_frame_packet , Data too long to fit into the buffer.sz: %u\n",packet_sz);
        return -1;
    }
    packet_index = packet_index & 0xFF;
    brocast_cmd[12] = packet_index++;

    length_offset += length;
    brocast_cmd[13] = (length_offset >> 8) & 0xFF;
    brocast_cmd[14] = length_offset & 0xFF;

    brocast_cmd[19] = (offset >> 24) & 0xFF;
    brocast_cmd[18] = (offset >> 16) & 0xFF;
    brocast_cmd[17] = (offset >>  8) & 0xFF;
    brocast_cmd[16] = offset & 0xFF;

    memcpy(combined_data,brocast_cmd,20);
    memcpy(combined_data+20,data,length);
    memcpy(combined_data+length+20,crc,4);

    if (send_raw_socket_packet(combined_data, packet_sz) == -1){
        printf("Sending failed");
        return -1;
    }

    return 1;
}

int send_frame_sync(void)
{
    unsigned char combined_data[MAX_DATA_LENGTH];
    uint8_t brocast_cmd[CMD_HEAD_SZ] = {
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, //Destination Address
        0x00, 0x00, 0x00, 0x00, 0x00, 0x01, //Source Address
        0x00, //Packet Index
        0x00, 0x00, //Number of Data Byte
        0x12, //Flow Ctrl
        0xCC,0xCC,0xCC,0xCC, //crc
    };

    packet_index = packet_index & 0xFF;
    brocast_cmd[12] = packet_index++;

    memcpy(combined_data,brocast_cmd,20);
    
    if (send_raw_socket_packet(combined_data, 20) == -1){
        printf("Sending failed");
        return -1;
    }

    return 1;
}
int send_rgb_frame_with_raw_socket(const unsigned char *rgb_frame, int frame_sz, unsigned int frame_id, bool need_delay)
{    
    unsigned int i = 0;
    unsigned int segment_length = 0;
    unsigned char raw_socket_packet[MAX_DATA_LENGTH];
    unsigned int offset = 0;
    unsigned int data_length = 0;
    struct timespec tim, tim2;
    tim.tv_sec = 0;
    tim.tv_nsec = 1;
    //nanosleep(&tim, NULL);

    if (frame_id > 0xffff) {
        printf("frame_id out of 0xffff\n");
        return -1;
    }
    
    while (i < frame_sz) {
       
        if(frame_sz - i > MAX_FRAME_SIZE)
            segment_length = MAX_FRAME_SIZE;
        else 
            segment_length = frame_sz -i;

        data_length = segment_length;
        
        if (data_length > MAX_DATA_LENGTH) {
            printf("Send rgb frame , Data too long to fit into the buffer. sz:%u \n",data_length);
            return -1;
        }
        
        memcpy(raw_socket_packet, rgb_frame + i, segment_length);
        send_frame_packet(raw_socket_packet, data_length, offset + 0x000F0000);
        offset +=data_length;

        if(need_delay == true){
            if(nanosleep(&tim, NULL)<0){
                printf("nsec sleep failed!\n");
            }
	    }
        i += MAX_FRAME_SIZE;
    }
    if(need_delay == true){
        if(nanosleep(&tim, &tim2)<0){
	        printf("nsec sleep failed!\n");
        }
    }
    send_frame_sync();
    return 1;
}
