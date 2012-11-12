/**
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

#ifndef STD_MANSOS_H
#define STD_MANSOS_H

// include all the things that could be useful

#include "mansos.h"

#include <sleep.h>
#include <alarms.h>
#include <digital.h>
#ifdef USE_ADC
#include <analog.h>
#endif
#ifdef USE_LEDS
#include <leds.h>
#endif
#ifdef USE_RADIO
#include <radio.h>
#endif
#ifdef USE_SERIAL
#include <serial.h>
#endif
#include <delay.h>
#include <timers.h>
#include <errors.h>
#ifdef USE_PRINT
#include <print.h>
#endif
#ifdef USE_ADDRESSING
#include <net/addr.h>
#endif
#ifdef USE_PROTOTHREADS
#include <kernel/protothreads/process.h>
#include <kernel/protothreads/autostart.h>
#include <kernel/protothreads/etimer.h>
#ifdef USE_RADIO
#include <kernel/protothreads/radio-process.h>
#endif
#endif
#include <utils.h>
#include <sensors.h>
#include <random.h>

#endif
