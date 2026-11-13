'''
@file rotor.py
@author Scott L. Williams
@package STaR
@brief Abstract class for rotors
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
Abstract class for rotors. Under consideration for deprecation.
Don't call directly. User must derive from this class 
and then supply motor control specifics. See examples in ../rotors.
Load specific motion control rotor class through the configurations file.
'''
rotor_copyright = 'rotor.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import time
import logging

from ezprint import eprint, eprints

# abstract class for antenna rotor. user should supply 
# state minimal routines, init parameters and communications.
# underlying pass motion strategies are implemented here based 
# on azimuth, elevation parameters the rotors have (not yet )
#

# somewhat unnecessary class as rotor modules can provide
# methods directly. however this class defines standard methods
# as to what the rotor modules should be providing 
class rotor():
    
    def __init__( self ):

        self.version = None         # rotor version, not star version
        self.name = None            # rotor name
        self.comm_addr = None       # communication address
        self.calib_duration = None  # time duration for initialization

        self.az_park = 0.0          # park position
        self.el_park = 90.0

        self.lead = 0.0             # time lead in seconds
                                    # used for sluggish response and look ahead

        self.az_offset = 0.0        # azimuth and elevation position offsets
        self.el_offset = 0.0

        self.az_min = None          # motion parameters
        self.az_max = None

        self.el_min = None
        self.el_max = None

        self.logger = None
        
    # reset rotor software params
    def reset( self ):
        pass                        # may not be required

    def report( self, message ):
        
        message = 'rotor.py: ' + message
        eprint( 'ERROR: ' + message )
        self.logger.error( message )
        sys.exit( 1 )
        
    # get rotor calibration status
    def is_calibrating( self ):
        message = 'is_calibrating: this method must be overridden ... exiting'
        self.report( message )
        
    # move to azimuth and elevation positions; override in subclass
    def move_azel( self, az, el, wait=False ):
        message = 'move_azel: this method must be overridden ... exiting'
        self.report( message )
        
    # read azimuth and elevation positions; override in subclass
    def get_azel( self  ):
        message = 'read_azel: this method must be overridden ... exiting'
        self.report( message )
        
    # move to azimuth position; override in subclass
    def move_az( self, az ):
        message = 'move_az: this method must be overridden ... exiting'
        self.report( message )
        
    # read azimuth position; override in subclass
    def read_az( self  ):
        message = 'read_az: this method must be overridden ... exiting'
        self.report( message )
        
    # move to elevation position; override in subclass
    def move_el( self, el ):
        message = 'move_el: this method must be overridden ... exiting'
        self.report( message )
        
    # read elevation position; override in subclass
    def read_el( self ):
        message = 'read_el: this method must be overridden ... exiting'
        self.report( message )
        
    # calibrate rotor motion control; override in subclass
    def initialize( self ):
        message =  'initialize: this method must be overridden ... exiting'
        self.report( message )
        
    # get rotor motion control status; override in subclass
    def status( self ):
        message = 'status: this method must be overridden ... exiting'
        self.report( message )
        
    # open rotor control
    def open( self ):
        message = 'open: this method must be overridden ... exiting'
        self.report( message )
        
    # close rotor control
    def close( self ):
        message = 'close: this method must be overridden ... exiting'
        self.report( message )

    # unwrap antenna wire
    def unwrap( self ):
        message = 'unwrap: this method must be overridden ... exiting' 
        self.report( message )

    # report rotor information
    def get_info( self ):
        message = 'get_info: this method must be overridden ... exiting'
        self.report( message )

    # return rotor tracker 
    def get_tracker( self, coord ):
        message = 'get_tracker: this method must be overridden ... exiting'
        self.report( message )

############################################################################

    # general routines 

    # park the antenna
    def park( self ):
 
        self.logger.info( 'rotor: parking antenna...' )
        self.move_azel( self.az_park, self.el_park )
        self.logger.info( 'rotor: antenna parked' )

