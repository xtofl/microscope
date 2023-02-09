#!/usr/bin/env python3

## Copyright (C) 2020 David Miguel Susano Pinto <carandraug@gmail.com>
## Copyright (C) 2023 Ian Dobbie <ian.dobbie@jhu.edu>
##
##
## This file is part of Microscope.
##
## Microscope is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Microscope is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Microscope.  If not, see <http://www.gnu.org/licenses/>.

"""Raspberry Pi Digital IO module.
"""

import contextlib
import re
import threading
import time
import typing
import logging

import microscope.abc

import RPi.GPIO as GPIO


#Support for async digital IO control on the Raspberryy Pi.
#Currently supports digital input and output via GPIO lines


# Use BCM GPIO references (naming convention for GPIO pins from Broadcom)
# instead of physical pin numbers on the Raspberry Pi board
GPIO.setmode(GPIO.BCM)
_logger = logging.getLogger(__name__)



class RPiDIO(microscope.abc.DigitalIO):
    '''Digital IO device implementation for a Raspberry Pi

    gpioMap input array maps line numbers to specific GPIO pins
    [GPIO pin, GPIO pin]
    [27,25,29,...]  line 0 in pin 27, 1 is pin 25 etc....

    gpioState input array maps output and input lines.
    True maps to output
    False maps to input

    with the gpioMap above [True,False,True,..] would map:
    27 to out, 
    25 to in 
    29 to out'''
    
    def __init__(self,gpioMap = [], gpioState = [], **kwargs):
        super().__init__(numLines=len(gpioMap),**kwargs)
        #setup io lines 1-n mapped to GPIO lines
        self._gpioMap=gpioMap
        self._IOMap=gpioState
        self._numLines=len(self._gpioMap)
        self._outputCache = [False]*self._numLines
        self.set_all_IO_state(self._IOMap)



    #functions needed

    def set_IO_state(self, line: int, state: bool) -> None:
        _logger.debug("Line %d set IO state %s"% (line,str(state)))
        if state:
            #true maps to output
            GPIO.setup(self._gpioMap[line],GPIO.OUT)
            self._IOMap[line] = True
            #restore state from cache.
            state=self._outputCache[line]
            GPIO.output(self._gpioMap[line],state)
        else:
            GPIO.setup(self._gpioMap[line],GPIO.IN)
            self._IOMap[line] = False

    def get_IO_state(self, line: int) -> bool:
        #returns
        #  True if the line is Output
        #  Flase if Input
        #  None in other cases (i2c, spi etc)
        pinmode=GPIO.gpio_function(self._gpioMap[line])
        if pinmode==GPIO.OUT:
            return True
        elif pinmode==GPIO.IN:
            return False
        return None

    def write_line(self,line: int, state: bool):
        #Do we need to check if the line can be written?
        _logger.debug("Line %d set IO state %s"% (line,str(state)))
        self._outputCache[line]=state
        GPIO.output(self._gpioMap[line],state)
        
    def read_line(self,line: int) -> bool:
        # Should we check if the line is set to input first?
        #If input read the real state
        if (not self._IOMap[line]):
            state=GPIO.input(self._gpioMap[line])
            _logger.debug("Line %d returns %s" % (line,str(state)))
            return state
        else:
            #line is an outout so returned cached state
            return self._outputCache[line]

    def _do_shutdown(self) -> None:
        pass
