'''
@file scheduler.py
@author Scott L. Williams
@package STaR
@brief Schedules satellites passes.
@section LICENSE 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

@section DESCRIPTION
Trigger tracking and signal read for satellite rise and set events by
predicting satellite passes using the "ephem" package.
'''

scheduler_copyright = 'scheduler.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import math
import ephem
import signal
import logging
import subprocess

from time import *
from ezprint import eprint
from threading import Thread

class scheduler( Thread ):
    
    def __init__ ( self, star ):
        Thread.__init__( self )

        self.star = star                      # parent class
        self.station = star.station           # station attributes
        self.sats = star.sats                 # active satellites
        self.num_passes = star.num_passes     # number of passes per active sat
        self.rotor = star.rotor               # antenna control
        self.zenith_min = star.zenith_min     # min zenith threshold for pass
        self.running = False
        self.tracking = False
        self.passes = None
        
        self.sig_elev = star.sig_elev

        # use the same logger name
        self.logger = logging.getLogger( 'star_logger' )
        
    def print_passes( self, passes ):
        
        n = len( passes[0] )                  # number of coordinate lines
        self.logger.info( 'scheduler: next pass: ' + passes[0][0][0] +    \
                          ' rise: '+str( ephem.localtime(passes[0][0][1]) )[:19] + \
                          ' set: '+str( ephem.localtime(passes[0][n-1][1]))[:19] ) 

    # assign two line elements to a satellite
    def get_elements( self, sat ):
       
        try:
            tle = open( sat.tlef, 'r' )
            
        except Exception  as e:
            eprint( 'ERROR: ' + str(e) )
            self.logger.error( str(e) )
            
            message = 'scheduler: get_elements: cannot open ' + \
                       sat.tlef + ' ... exiting'
            eprint( 'ERROR: ' + message )
            self.logger.error( message )
            sys.exit( 1 )

        # find TLEs
        line = tle.readline()
        while line:                       # use satellite name as key
            if sat.name in line:
                sat.tle1 = tle.readline() # load values  
                sat.tle2 = tle.readline()
                tle.close()
                return                    # successful read
            
            line = tle.readline()
            
        self.logger.error( 'scheduler: cannot find TLEs for ' + sat.name +
                       ' in file: ' + sat.tlef + ' ... exiting.')
        tle.close()
        sys.exit(1)

    # sort passes by time and overlaps
    # pyephem uses float days from 12:00pm Dec.31, 1899 
    # while python uses integer seconds from 12:00am Jan.1, 1970
    def sort_passes( self, passes ):        
        num = len( passes )

        # sort passes in time based on first line date
        try:
            passes.sort( key=lambda x:x[0][1] )  
        except:
            # FIXME: keep this here to debug sort exception; considered fixed
            eprint( 'HELP',  num, len( passes[0]) )
            sys.exit(1)

        # check for overlap passes
        i=0
        while i < num:

            # calculate pass duration + buffer to allow for repositioning
            last_coord = len(passes[i])-1  # get last coordinate index

            # first come, first serve
            tr = passes[i][0][1]           # get rise and set times
            ts = passes[i][last_coord][1]

            j = i+1
            while j < num:
                next_tr = passes[j][0][1]

                # workaround for duplicate passes; FIXME: why duplicates?
                if (str(next_tr) == str(tr) ) and \
                   (passes[j][0][0] == passes[i][0][0] ):

                    # NOTE: utc time, not local time
                    self.logger.info( 'scheduler: duplicate pass: ' +
                                      passes[j][0][0] + 
                                      ' ' + str(tr) + ' ' + str(next_tr) +
                                      ' ' + str(i) + ' '  + str(j) )

                    passes.pop(j)          # remove duplicate pass
                    num -= 1               # keep track of pops
                    j -= 1

                elif next_tr > tr and next_tr < ts:

                    self.logger.info( 'scheduler: ' + passes[j][0][0] +
                                      ' overlaps ' + 
                                  passes[i][0][0] + ' at ' +       
                                  str(ephem.localtime(next_tr))[:19] + 
                                  ', removed from schedule.' )

                    passes.pop(j)          # remove later pass
                    num -= 1               # keep track of pops
                    j -= 1

                j += 1
            i += 1

        return passes

    # create a list of passes
    def predict_passes( self ):

        station = ephem.Observer()         # load ground station location
        station.lat = self.station.lat
        station.lon = self.station.lon
        station.elevation = self.station.alt
        station.pressure = 0               # set pressure to zero to match
                                           # spg4 predicted rise values.
                                           # has to do with atmos refraction.

        for i in range( len(self.sats) ):  # update keplerians for each sat
            self.get_elements( self.sats[i] ) 

        passes = []                        # satellite pass list
        for i in range( len(self.sats) ):  # active satellites
            
            bird = ephem.readtle( self.sats[i].name, 
                                  self.sats[i].tle1, self.sats[i].tle2 )

            # set station date to current date plus buffer time.
            # buffer time is needed for next pass antenna positioning.
            station.date = ephem.now() + ephem.minute
            bird.compute( station )
            
            # loop through potential passes for high enough zeniths
            p = 0
            while p < self.num_passes:
                
                # find the next pass
                tr, azr, tt, altt, ts, azs = station.next_pass( bird )

                # KLUDGE: workaround for bad next_pass values.
                # FIXME: should be able to pick up track on active pass
                # next_pass even chokes when asking for a pass close 
                # in time to the pass (about 45 min?) or during an existing pass
                # is this true?

                if tr >= ts: 
                    #print 'LESS', tr, ts, bird, math.degrees( altt )
                    station.date = ephem.now() + 20*ephem.minute
                    continue

                # check if pass elevation is high enough
                if math.degrees( altt ) < self.zenith_min:
                    station.date = ts + ephem.minute  # reset date
                    #print tr, ts, bird, math.degrees( altt )
                else:                      # a list of 
                                           # coordinates by incrementing time.
                    pas = []                    
                    while tr <= ts:        # construct up to setting time
                        station.date = tr  
                        bird.compute( station )

                        # load coordinates into list
                        coord = [ self.sats[i].name, tr,
                                  math.degrees(bird.az), 
                                  math.degrees(bird.alt) ]

                        pas.append( coord )

                        # increment time 
                        tr = ephem.Date( tr + 2.0*ephem.second ) #1.75

                    if len( pas ) > 0:                # do not append 
                        passes.append( pas )          # an empty list.
                        p += 1                        # FIXME: consider
                                                      # minimal size.
                    station.date = ts + 2.0*ephem.minute  # reset date.

        return self.sort_passes( passes )

    # return scripts associated with satellite name
    def get_scripts( self, name ):

        # find index to name in sats
        for i in range( len(self.sats) ):
            if name == self.sats[i].name:
                break

        return self.sats[i].read, self.sats[i].proc

    def stop( self ):           # end thread
        self.running = False

    def run ( self ):           # run thread
        self.running = True

        # get a list of next passes.
        # use just the first pass on the list for tracking
        # but make future passes available for gui.
        self.passes = self.predict_passes()
        self.print_passes( self.passes )
        self.star.update_passes = True

        # set readable variables
        n = len( self.passes[0] )               # number of coordinate lines
        srise = self.passes[0][0][1]            # satellite rise
        sset = self.passes[0][n-1][1]           # satellite set
        name = self.passes[0][0][0]             # satellite name

        read, proc = self.get_scripts( name )   # scripts to use

        # wait for next pass, then trigger track and read events
        self.tracking = False   # report to other threads if tracking
        prepositioned = False
        reading = False
        track = None
        enabled = True
        p = None
        
        while self.running:

            if not self.tracking:                        # wait for satellite
                if ephem.now() >= srise - 90*ephem.second: # allow 90 seconds to
                    if not prepositioned:                # preposition antenna

                        # start rotor tracking thread
                        self.logger.info( 'scheduler: starting tracker thread' )
                        track = self.rotor.get_tracker( self.passes[0] )
                        track.start()

                        prepositioned = True

                if ephem.now() >= srise:               # flag tracking
                    self.tracking = True               
                    prepositioned = False
                    self.logger.info( 'scheduler: antenna is tracking...' )
            else:
                # we are tracking

                # check if we can start signal read
                if not reading and enabled:

                    # get current elevation
                    az, el = self.rotor.get_azel()
                    if el > self.sig_elev:  
                                            
                        # invoke read script
                        self.logger.info( 'scheduler: starting signal read command: ' + read )
                        try:
                            p = subprocess.Popen( 'exec ' + read, shell=True )
                        except:
                            # keep going anyway
                            self.logger.error( 'scheduler: cannot start signal read' )
                        reading = True
                        sleep(2.0)    # let the motors and threads settle 
                                      # motor ocillations can trigger
                                      # signal read stop eg. el < self.sig_elev
                                      # if threads do not report in time
                                      # can also trigger

                        
                # check if signal read should stop
                if reading:

                    # get current elevation
                    az, el = self.rotor.get_azel()
                    #print( '%5.1f'%el, '%5.1f'%self.sig_elev )
                    # FIXME: check antenna mode and
                    #        adjust sig_elev if mode=ZENITH.
                    #        do it outside loop.
                    if el < self.sig_elev:
                        self.logger.info( 'scheduler: stopping signal read' )
                        try:
                            p.kill()
                            p.wait()
                        except:                            
                            self.logger.error( 'scheduler: error in stopping read process' )
                            # keep going
                            
                        # invoke post acquisition processing here
                        self.logger.info( 'scheduler: starting processing command: ' + proc )
                        script = proc.split()            # parse out arguments.
                        try:
                            subprocess.Popen( script )   # don't need pid, 
                        except:
                            self.logger.error( 'scheduler: cannot start processing' )
                            # keep going

                        reading = False
                        enabled = False
                        
                # check to see if satellite has set
                # FIXME: should check if signal read has stopped
                #        if so, then motion is too slow
                if ephem.now() > sset:              
                    self.tracking = False             # stop tracking
                    enabled = True
                    p = None
                    
                    # stop rotor tracking thread
                    self.logger.info( 'scheduler: stopping tracker thread' )
                    if track.running == True:
                        track.stop()                   # wait for tracker  
                        track.join()                   # to stop.
                        track = None                   # clear it out
                                                       
                    # prepare for next pass
                    self.passes = self.predict_passes()
                    self.print_passes( self.passes )
                    self.star.update_passlist = True   # signal parent to 
                                                       # refresh pass list (gui)
                    # recharge 
                    n = len( self.passes[0] )          # number of coord lines
                    srise = self.passes[0][0][1]       # grab rise and set times
                    sset = self.passes[0][n-1][1]
                    name = self.passes[0][0][0]        # satellite name

                    read, proc = self.get_scripts( name )
                    
            sleep( 1.0 )                               # refresh every 
                                                       # 1 second 
        # clean up tracking thread
        if track != None:
            if track.running == True:
                track.stop()
                track.join()
