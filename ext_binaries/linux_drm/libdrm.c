#include <fcntl.h>
#include <unistd.h>
#include <xf86drm.h>
#include <xf86drmMode.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <string.h>
#include <errno.h>
#include <sys/ioctl.h>


#define USE_DMA_BUF     1  // 1: Use DMA-BUF if available, 0: Try Dumb Buffer
#define USE_DUMB_BUFFER 1  // 1: Use Dumb Buffer if DMA-BUF fails


static int drm_fd = -1;
static drmModeRes *resources = NULL;
static drmModeCrtc *crtc = NULL;
static drmModeFB *fb = NULL;
static void *mapped_fb = NULL;
static size_t fb_size = 0;

static int use_dma_buf = 0;  
static int dma_buf_fd = -1;  

static int bytes_per_pixel = 0;
static int src_stride = 0;
static int dest_stride = 0;


typedef enum {
    COLOR_SPACE_ABGR,
    COLOR_SPACE_RGB888
} ColorSpace;

static ColorSpace current_color_space = COLOR_SPACE_ABGR;

int drm_initialize(const char *device_path, int assign_crt_index) 
{
    drm_fd = open(device_path, O_RDWR);
    if (drm_fd < 0) {
        perror("Failed to open DRM device");
        return -1;
    }

    resources = drmModeGetResources(drm_fd);
    if (!resources) {
        perror("Failed to get DRM resources");
        close(drm_fd);
        return -1;
    }

    if (assign_crt_index >= 0) {
        crtc = drmModeGetCrtc(drm_fd, resources->crtcs[assign_crt_index]);

        if (!crtc || crtc->buffer_id == 0) {
            fprintf(stderr, "No active CRTC with framebuffer found.\n");
            drmModeFreeResources(resources);
            close(drm_fd);
            return -1;
        }
    } else {
        for (int i = 0; i < resources->count_crtcs; i++) {
            crtc = drmModeGetCrtc(drm_fd, resources->crtcs[i]);
            if (crtc && crtc->buffer_id != 0) {
                printf("Using CRTC %d\n", resources->crtcs[i]);
                break;
            }
            if (crtc) drmModeFreeCrtc(crtc);
        }
        if (!crtc) {
            fprintf(stderr, "No active CRTC found.\n");
            drmModeFreeResources(resources);
            close(drm_fd);
            return -1;
        }
    }

    if (crtc->buffer_id == 0) {
        printf("No framebuffer associated with the CRTC.\n");
        drmModeFreeCrtc(crtc);
        drmModeFreeResources(resources);
        close(drm_fd);
        return -1;
    }

    fb = drmModeGetFB(drm_fd, crtc->buffer_id);
    if (!fb) {
        perror("Failed to get framebuffer");
        drmModeFreeCrtc(crtc);
        drmModeFreeResources(resources);
        close(drm_fd);
        return -1;
    }
    printf("Trying to use framebuffer ID: %d\n", crtc->buffer_id);

    if (USE_DMA_BUF) {
        if (drmPrimeHandleToFD(drm_fd, fb->handle, 0, &dma_buf_fd) == 0) {
            printf("Using DMA-BUF method\n");
            use_dma_buf = 1;
            mapped_fb = mmap(NULL, fb->pitch * fb->height, PROT_READ, MAP_SHARED, dma_buf_fd, 0);
            if (mapped_fb == MAP_FAILED) {
                perror("Failed to mmap DMA-BUF framebuffer");
                close(dma_buf_fd);
                return -1;
            }
            printf("Successfully mapped DMA-BUF framebuffer\n");
            return 0;
        } else {
            printf("DMA-BUF not available, falling back to dumb buffer\n");
        }
    }

    if (USE_DUMB_BUFFER) {
        struct drm_mode_map_dumb map_dumb = {0};
        map_dumb.handle = fb->handle;
        if (ioctl(drm_fd, DRM_IOCTL_MODE_MAP_DUMB, &map_dumb) < 0) {
            perror("Failed to map dumb buffer");
            return -1;
        }

        fb_size = fb->pitch * fb->height;
        mapped_fb = mmap(NULL, fb_size, PROT_READ, MAP_SHARED, drm_fd, map_dumb.offset);
        if (mapped_fb == MAP_FAILED) {
            perror("Failed to mmap framebuffer");
            return -1;
        }
        printf("Successfully mapped dumb buffer\n");
    }

    return 0;
}

void drm_cleanup(void) 
{
    if (mapped_fb) munmap(mapped_fb, fb_size);
    if (fb) drmModeFreeFB(fb);
    if (crtc) drmModeFreeCrtc(crtc);
    if (resources) drmModeFreeResources(resources);
    if (dma_buf_fd >= 0) close(dma_buf_fd); 
    if (drm_fd >= 0) close(drm_fd);
}

void drm_capture_format(int width, int height, int px_size) 
{
    if (width <= 0 || height <= 0 || px_size <= 0) {
        fprintf(stderr, "Invalid capture format dimensions or pixel size.\n");
        return;
    }
    bytes_per_pixel = px_size;
    src_stride = fb->pitch;
    dest_stride = width * bytes_per_pixel;
    printf("Capture format set: Width: %d, Height: %d, Bytes per Pixel: %d\n", width, height, bytes_per_pixel);
}    

void drm_set_color_space(const char *color_space) 
{
    if (strcmp(color_space, "ABGR") == 0) {
        current_color_space = COLOR_SPACE_ABGR;
        printf("Color space set to ABGR\n");
    } else if (strcmp(color_space, "RGB") == 0) {
        current_color_space = COLOR_SPACE_RGB888;
        printf("Color space set to RGB888\n");
    } else {
        fprintf(stderr, "Invalid color space: %s\n", color_space);
    }
}

int drm_capture_frame(uint8_t *dest_buffer, int x_offset, int y_offset, int width, int height)
{
    if (!mapped_fb || !fb) {
        fprintf(stderr, "DRM is not initialized.\n");
        return -1;
    }

    if (x_offset + width > fb->width || y_offset + height > fb->height) {
        fprintf(stderr, "Capture dimensions exceed framebuffer bounds.\n");
        return -1;
    }

    if (current_color_space == COLOR_SPACE_RGB888) {
        for (int y = 0; y < height; y++) {
            uint8_t *src_row = (uint8_t *)mapped_fb + (y + y_offset) * src_stride + x_offset * bytes_per_pixel;
            uint8_t *dest_row = dest_buffer + y * dest_stride;
            for (int x = 0; x < width; x++) {
                uint8_t b = src_row[x * bytes_per_pixel];
                uint8_t g = src_row[x * bytes_per_pixel + 1];
                uint8_t r = src_row[x * bytes_per_pixel + 2];

                dest_row[x * 3] = r;
                dest_row[x * 3 + 1] = g;
                dest_row[x * 3 + 2] = b;
            }
        }
    } else {
        for (int y = 0; y < height; y++) {
            memcpy(dest_buffer + y * dest_stride,
                   (uint8_t *)mapped_fb + (y + y_offset) * src_stride + x_offset * bytes_per_pixel,
                   dest_stride);
        }
    }

    return 0;
}
