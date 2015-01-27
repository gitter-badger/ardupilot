
#ifndef __AP_HAL_AVR_SITL_MAIN_H__
#define __AP_HAL_AVR_SITL_MAIN_H__

#include <signal.h>
#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>

#include "error.h"

#if CONFIG_HAL_BOARD == HAL_BOARD_AVR_SITL
#define AP_HAL_MAIN() extern "C" {\
    int main (int argc, char * const argv[]) {	\
        icky_global_program_name = argv[0]; \
        ERROR::set_signal_handler(); \
	    hal.init(argc, argv); \
        setup(); \
        hal.scheduler->system_initialized(); \
        for(;;) { \
    		loop(); \
    		AVR_SITL::SITL_State::loop_hook(); \
	    } \
        return 0;\
    }\
}
#endif

#endif // __AP_HAL_AVR_SITL_MAIN_H__
