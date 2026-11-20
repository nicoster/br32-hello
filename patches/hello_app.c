/* hello_app.c — minimal Flash-resident hello world for BR23 SDK.
 * Kept alive as an independent SDK task; does not touch USB/update code.
 */
#include "system/includes.h"
#include "system/task.h"
#include "app_config.h"

#define LOG_TAG_CONST       APP
#define LOG_TAG             "[HELLO]"
#define LOG_INFO_ENABLE
#include "debug.h"

static void hello_task(void *arg)
{
    u32 n = 0;
    while (1) {
        log_info("hello world #%u  (AC695N SDK, flash build)", n);
        n++;
        os_time_dly(100);           /* 100 ticks = 1 s (100 Hz tick) */
    }
}

void hello_app_init(void)
{
    task_create(hello_task, NULL, "hello");
}
