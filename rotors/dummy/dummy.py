'''
@file dummy.py
@author Scott L. Williams
@package STaR
@brief A dummy rotor for STaR
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
A dummy rotor for STaR. Exercises STaR for testing purposes. Can also
write satellite track position to file.
'''

dummy_copyright = 'dummy.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import sys
import time
import ephem
import logging

from rotor import rotor
from ezprint import eprint
from threading import Thread

# return an instance of 'dummy' class 
# without having to know its name
def instantiate( name, el_offset, az_offset, lead ):
    return dummy( name, el_offset, az_offset, lead )

class dummy( rotor ):
    
    def __init__( self, name, el_offset, az_offset, lead ):

        rotor.__init__( self )        # initialize base class first

        self.version = '2020.000'
        self.name = name              # module's name
        
        self.el = None
        self.el_offset = el_offset    # elevation offset

        self.az = None
        self.az_offset = az_offset    # azimuth elevation
        
        self.lead = lead              # lead time in seconds
        self.el_park = 90.0           # park position
        self.az_park = 0.0

        # use the same logger name
        self.logger = logging.getLogger( 'star_logger' )
        self.logger.info( 'logger initialized in dummy' )

        self.logger.info( 'using rotor ' + self.name +
                          ' version ' + self.version )

        # set this up for dummy rotor only
        self.timer = 0                # used to simulate calibration
        self.calib_duration = 10      # time it takes to calibrate rig
        
    def calibrate( self ):            # calibrate the rotors
        self.timer = 10

    def is_calibrating( self ):
        
        if self.timer > 0:
            self.timer -= 1
            return True

        return False

    # move to azimuth and elevation positions
    def move_azel( self, az, el ):

        # adjust according to setup
        self.az = az + self.az_offset
        self.el = el + self.el_offset
        
    # read azimuth and elevation positions
    def get_azel( self  ):
        
        az = self.az - self.az_offset
        el = self.el - self.el_offset
        return az, el

    def open( self, comm_addr ):
        pass

    def get_info( self ):
        return 'dummy rotor version: ' + self.version

    def get_tracker( self, coord ):
        return( dummy_tracker(self,coord) )

# end class dummy

# rotor tracker thread; customized tracker for dummy rotors 
class dummy_tracker( Thread ):
    def __init__ ( self, rotor, coord ):
        Thread.__init__( self )

        self.rotor = rotor           # antenna control.
        self.coord = coord           # list of coordinates (time, az, el)
                                     # for this pass.
        self.running = False         # flag to stop thread

        self.num = len( self.coord )        # number of track points

    def stop( self ):
        self.running = False

    def clean_up( self ):       

        self.rotor.park()
        self.running = False

    def run ( self ):
        
        self.running = True
        lead = self.rotor.lead*ephem.second

        '''
        try:
            # write track coordinates to file
            stamp = time.strftime('%H:%M:%S')
            f = open( 'track_'+stamp+'.txt', 'w' )
            for i in range( 0, num ):
                f.write( str(self.coord[i][1])[10:] +
                         ' %5.3f'%self.coord[i][2] +
                         ' %5.3f\n'%self.coord[i][3] )
            f.close()
        except:
            print('could not write track to file', file=sys.stderr, flush=True)
        '''

        # find first future index into pass coordinate list
        for i in range( 0, self.num ):
            if self.coord[i][1] > (ephem.now() + lead):
                break

        if i == self.num-1:
            self.logger.warning( 'tracker:run: pass coordinates ' +
                             'are in the past. nothing to track. ' +
                             'exiting tracker thread...' )
            self.running = False
            return               # nothing to do

        # go to start position    
        self.logger.info( 'moving antenna to rise position: ' +   \
                          '%5.1f'%self.coord[i][2] + ' ' \
                          '%5.1f'%self.coord[i][3] )

        self.rotor.move_azel( self.coord[i][2],self.coord[i][3] )
        
        while self.running:

            # skip to next time slot
            while self.coord[i][1] < (ephem.now() + lead):
               i += 1
               if i == self.num:    # end of pass coordinates
                self.logger.info( 'end of satellite pass' )
                self.clean_up()
                return              # end of thread

            # wait for next move, including antenna lead time.
            while self.coord[i][1] >= (ephem.now() + lead):
                time.sleep( 0.1 )
                if not self.running:
                    self.clean_up()
                    return       # end of thread

            self.rotor.move_azel( self.coord[i][2],   # step position
                                  self.coord[i][3] )

        self.clean_up()

# end class dummy_tracker

# end dummy.py
