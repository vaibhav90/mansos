# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2012 the MansOS team. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice,
#    this list of  conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import threading
import time

from globals import * #@UnusedWildImport

class ThreadRunner (threading.Thread):
    def __init__(self, function, dataIn, dataOut, API):
        threading.Thread.__init__(self)
        self.function = function
        # If mutable value passed it works as reference, so we can pass values back
        self.dataIn = dataIn
        self.dataOut = dataOut
        self.API = API

    def run (self):
        locTime = time.time()
        #try:
        self.dataOut += self.function(self.dataIn)
        #except TypeError:
        #    self.API.logMsg(LOG_WARNING, "In thread running " + str(self.function) + "type mismatch happened!")
        #    self.dataOut += [False, "Type error!"]
        #    print self.function()
        self.dataOut += [time.time() - locTime]

