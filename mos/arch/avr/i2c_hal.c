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

/*
 * ATMega 2-wire is I2C-compatible
 */

#include <hil/i2c.h>
#include "atmega/atmega_2wire.h"

/**
 * Initializes the I2C bus
 */
void i2cInit() {
    twiInit();
}

/**
 * Turn on the I2C bus
 */
void i2cOn() {
    twiOn();
}

/**
 * Turn off the I2C bus
 */
void i2cOff() {
    twiOff();
}


/**
 * Writes a byte to I2C and checks acknowledge
 * @param   addr    address of the slave receiver
 * @param   txByte  byte to transmit
 * @return          0 on success, error code otherwise
 */
i2cError_t i2cWriteByte(uint8_t addr, uint8_t txByte) {
    return twiWrite(addr, &txByte, 1, 1);
}

/*
 * Writes a string to I2C and checks acknowledge
 * @param   addr    address of the slave receiver
 * @param   buf     the buffer containing the string
 * @param   len     buffer length in bytes
 * @return  0       on success, error code otherwise
 */
uint8_t i2cWrite(uint8_t addr, const void *buf, uint8_t len) {
    return twiWrite(addr, buf, len, 1);
}

/*
 * Reads a byte from I2C - requests it from a slave
 * @param   addr    address of the slave transmitter
 * @param   rxByte  buffer, where the received data will be stored
 * @return  received byte count (1 on success, 0 on error)
 */
uint8_t i2cReadByte(uint8_t addr, uint8_t *rxByte) {
    return twiRead(addr, rxByte, 1);
}

/*
 * Reads a message into buffer from I2C - requests it from a slave
 * @param   addr    address of the slave transmitter
 * @param   buf     the buffer to store the message
 * @param   len     buffer length in bytes
 * @return  received byte count
 */
uint8_t i2cRead(uint8_t addr, void *buf, uint8_t len) {
    return twiRead(addr, buf, len);
}