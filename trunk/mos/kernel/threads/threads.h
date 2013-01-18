/*
 * Copyright (c) 2008-2012 the MansOS team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *  * Redistributions of source code must retain the above copyright notice,
 *    this list of  conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef MANSOS_THREADS_H
#define MANSOS_THREADS_H

#include <kernel/defines.h>
#include "timing.h"
#include <lib/assert.h>
#include <platform.h>

#ifndef NUM_USER_THREADS
#define NUM_USER_THREADS 1
#endif
#define NUM_THREADS (NUM_USER_THREADS + 1)

// it's the last one
#define KERNEL_THREAD_INDEX (NUM_THREADS - 1)

#if PLATFORM_FARMMOTE
#define THREAD_STACK_SIZE 128
#elif PLATFORM_ARDUINO
#define THREAD_STACK_SIZE 256
#else
#define THREAD_STACK_SIZE 512
#endif

#if DEBUG
#define DEBUG_THREADS 1
#endif

#define SCHEDULING_POLICY_ROUND_ROBIN    1
#define SCHEDULING_POLICY_PRIORITY_BASED 2

#ifndef SCHEDULING_POLICY
#define SCHEDULING_POLICY SCHEDULING_POLICY_ROUND_ROBIN
#endif

#if DEBUG_THREADS
#define SAVE_THREAD_LAST_RUN_TIME 1
#endif
#if NUM_USER_THREADS > 1
#if SCHEDULING_POLICY == SCHEDULING_POLICY_ROUND_ROBIN
#define SAVE_THREAD_LAST_RUN_TIME 1
#endif
#endif


// ----------------------------------------------------------------
// Types
// ----------------------------------------------------------------

typedef void (*ThreadFunc)(void);

enum ThreadState_e {
    THREAD_UNUSED,
    THREAD_BLOCKED,
    THREAD_SLEEPING,
    THREAD_READY,
    THREAD_RUNNING,
} PACKED;

typedef enum ThreadState_e ThreadState_t;

typedef struct Thread_s {
    MemoryAddress_t sp;     // stack pointer
    uint8_t index;          // thread number
    uint8_t priority;       // threads with larger priority are run first
    ThreadState_t state;    // state (running, ready, etc.)
    ThreadFunc function;    // thread start function
    uint32_t sleepEndTime;  // in jiffies, defined when state is THREAD_SLEEPING
#if SAVE_THREAD_LAST_RUN_TIME
    uint32_t lastSeenRunning; // used for lockup detection, and for scheduling
#endif
} Thread_t;

typedef union {
    uint8_t value;
    struct {
        uint8_t alarmsProcess : 1;
        uint8_t radioProcess : 1;
    } bits;
} ProcessFlags_t;

// ----------------------------------------------------------------
// Macros
// ----------------------------------------------------------------

// something like this default value is used by compilers (GCC and IAR)
#define KERNEL_STACK_BOTTOM  ((MemoryAddress_t)0x3800)

#define STACK_ADDR_LOW()                                                \
    (currentThread->index == KERNEL_THREAD_INDEX ?                      \
            KERNEL_STACK_BOTTOM :                                       \
            (MemoryAddress_t)threadStackBuffer + (currentThread->index * THREAD_STACK_SIZE))

#if USE_THREADS
#define STACK_GUARD() do {                                         \
        /* declare a stack pointer variable */                     \
        MemoryAddress_t currentSp;                                 \
        /* read the current stack pointer into the variable */     \
        GET_SP(currentSp);                                         \
        /* compare the current stack pointer with stack bottom */  \
        /* and abort in case of overflow */                        \
        ASSERT_NOSTACK(currentSp >= STACK_ADDR_LOW());             \
    } while (0)
#else
#define STACK_GUARD()
#endif

// ----------------------------------------------------------------
// Global variables
// ----------------------------------------------------------------

extern uint16_t jiffiesToSleep;

extern ProcessFlags_t processFlags;

// the active (running) thread
extern Thread_t *currentThread;

// exported to global context only for debugging
extern uint8_t threadStackBuffer[];

// ----------------------------------------------------------------
// System-only API
// ----------------------------------------------------------------

//
// This is the main scheduling function.
// Depending on thread status and the value of global variable 'jiffiesToSleep', it can:
// * switch to a new thread
// * keep running the current thread, if 'jiffiesToSleep' is 0, and no other thread are ready
// * enter low power mode, if all threads are in sleeping state
//
void schedule(void) NAKED;

void threadCreate(uint_t threadIndex, ThreadFunc threadFunction);

void startThreads(ThreadFunc userThreadFunction, ThreadFunc kernelThreadFunction);

void threadWakeup(uint16_t threadIndex, ThreadState_t newState);

//
// This function implements the system's main loop
//
void systemMain(void) NORETURN;

// Maximal supported sleeping time for telosb is 15984 msec;
// Even if the user schedules longer sleeping interval,
// the kernel will wake up after this much time in any case.
// (Of course, both alarms and msleep() support larger sleep times, but only logically!)
#ifndef MAX_KERNEL_SLEEP_TIME
#define MAX_KERNEL_SLEEP_TIME PLATFORM_MAX_SLEEP_MS
#endif

#if DEBUG_THREADS
#define LOCKUP_DETECT_TIME  3000
void checkThreadLockups(void);
#endif

static inline void setSeenRunning(Thread_t *t) {
#if SAVE_THREAD_LAST_RUN_TIME
    t->lastSeenRunning = getJiffies();
#endif
}

static inline uint32_t getLastSeenRunning(Thread_t *t) {
#if SAVE_THREAD_LAST_RUN_TIME
    return t->lastSeenRunning;
#else
    return 0;
#endif
}

static inline void setPriority(Thread_t *t, uint8_t priority) {
#if SCHEDULING_POLICY == SCHEDULING_POLICY_PRIORITY_BASED
    t->priority = priority;
#endif
}

// ----------------------------------------------------------------
// User API
// ----------------------------------------------------------------

//
// Put current thread to sleep for a specific time
//
static inline void msleep(uint16_t ms)
{
    while (ms > PLATFORM_MAX_SLEEP_MS) {
        jiffiesToSleep = ms2jiffies(PLATFORM_MAX_SLEEP_MS);
        ms -= PLATFORM_MAX_SLEEP_MS;
        schedule();
    }
    jiffiesToSleep = ms2jiffies(ms);
    schedule();
}

//
// Switch to a different thread, if any is ready
//
static inline void yield()
{
    jiffiesToSleep = 0;
    schedule();
}

#endif
