/*This is the sample program to notify us for the file creation and file deletion takes place in “/tmp” directory*/
#include "fs_inotify.h"

#define EVENT_SIZE  ( sizeof (struct inotify_event) )
#define EVENT_BUF_LEN     ( 1024 * ( EVENT_SIZE + 16 ) )

void* fs_inotify(void* args);

#define MACHINE_TYPE_Pi4    0
#define MACHINE_TYPE_Pi5    1

void* fs_inotify(void* args){
  	int length, i = 0;
  	int fd;
  	int wd;
  	char buffer[EVENT_BUF_LEN];
    struct utsname unameData;

  	int machine_type = 0;

  	uname(&unameData);
    if(strstr(unameData.nodename, "pi4" )){
        machine_type = MACHINE_TYPE_Pi4;
    }else{
        machine_type = MACHINE_TYPE_Pi5;
    }
    printf("machine_type : %d\n", machine_type);


  	/*creating the INOTIFY instance*/
  	fd = inotify_init();

	while (true){
  		/*creating the INOTIFY instance*/
  		//fd = inotify_init();
		
		i = 0;

  		/*checking for error*/
  		if ( fd < 0 ) {
    			perror( "inotify_init" );
  		}

  		/*adding the “/tmp” directory into watch list. Here, the suggestion is to validate the existence of the directory before adding into monitoring list.*/
  		wd = inotify_add_watch( fd, "/home/venom/sandbox/inotify/", IN_CREATE | IN_DELETE | IN_MODIFY);

  		/*read to determine the event change happens on “/tmp” directory. Actually this read blocks until the change event occurs*/ 

  		length = read( fd, buffer, EVENT_BUF_LEN ); 

  		/*checking for error*/
  		if ( length < 0 ) {
    			perror( "read" );
  		}  

  		/*actually read return the list of change events happens. Here, read the change event one by one and process it accordingly.*/
  		while ( i < length ) {     
			struct inotify_event *event = ( struct inotify_event * ) &buffer[ i ];     
			printf("event->len : %d\n", event->len);
			if ( event->len ) {
      				if ( event->mask & IN_CREATE ) {
        				if ( event->mask & IN_ISDIR ) {
          					printf( "New directory %s created.\n", event->name );
        				}else {
          					printf( "New file %s created.\n", event->name );
        				}
      				}else if ( event->mask & IN_DELETE ) {
        				if ( event->mask & IN_ISDIR ) {
          					printf( "Directory %s deleted.\n", event->name );
        				}else {
          					printf( "File %s deleted.\n", event->name );
        				}
      				}else if (event->mask & IN_MODIFY){
        				if ( event->mask & IN_ISDIR ) {
          					printf( "Directory %s modified.\n", event->name );
        				}else {
          					printf( "File %s modified.\n", event->name );
        				}
      				}
    			}
    			i += EVENT_SIZE + event->len;
  		}
  		/*removing the “/tmp” directory from the watch list.*/
   		//inotify_rm_watch( fd, wd );

  		/*closing the INOTIFY instance*/
   		//close( fd );
	}
  	/*removing the “/tmp” directory from the watch list.*/
   	inotify_rm_watch( fd, wd );

  	/*closing the INOTIFY instance*/
   	close( fd );

}


/*int main(int argc, char* argv[] ){
	pthread_t t;
	pthread_create(&t, NULL, fs_inotify, "fs_inotify");

	while(true){
		sleep(2);
		printf("sleep!\n");
	}

}*/
