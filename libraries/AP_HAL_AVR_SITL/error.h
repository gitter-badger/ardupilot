#ifndef __ERROR_H__
#define __ERROR_H__

#include <signal.h>
#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>

class ERROR {
	public:
		static void set_signal_handler();
};

void posix_signal_handler(int sig, siginfo_t *siginfo, void *context);
int addr2line(char const * const program_name, void const * const addr);
void posix_print_stack_trace();

extern char const * icky_global_program_name;

#endif