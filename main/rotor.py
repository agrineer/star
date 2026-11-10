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
# as to what is the rotor modules should be providing 
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

    # reset rotor software params
    def reset( self ):
        pass                        # may not be required

    # get rotor calibration status
    def is_calibrating( self ):
        eprint('ERROR: is_calibrating: this method must be overridden' )

    # move to azimuth and elevation positions; override in subclass
    def move_azel( self, az, el, wait=False ):
        eprint('ERROR: move_azel:this method must be overridden' )

    # read azimuth and elevation positions; override in subclass
    def get_azel( self  ):
        eprint('ERROR: read_azel:this method must be overridden' )
        return None,None

    # move to azimuth position; override in subclass
    def move_az( self, az ):
        eprint('ERROR: move_az:this method must be overridden' )

    # read azimuth position; override in subclass
    def read_az( self  ):
        eprint('ERROR: read_az:this method must be overridden' )
        return None

    # move to elevation position; override in subclass
    def move_el( self, el ):
        eprint('ERROR: move_el:this method must be overridden' )

    # read elevation position; override in subclass
    def read_el( self ):
        eprint('ERROR: read_el:this method must be overridden' )
        return None

    # calibrate rotor motion control; override in subclass
    def initialize( self ):
        eprint('ERROR: initilaize:this method must be overridden' )
        return None

    # get rotor motion control status; override in subclass
    def status( self ):
        eprint('ERROR: status:this method must be overridden' )
        return None, None, None

    # open rotor control
    def open( self ):
        eprint('ERROR: open:this method must be overridden' )
        return None

    # close rotor control
    def close( self ):
        eprint('ERROR: close:this method must be overridden' )
        return None

    # unwrap antenna wire
    def unwrap( self ):
        eprint('ERROR: unwrap:this method must be overridden' )

    # report rotor information
    def get_info( self ):
        eprint('ERROR: get_info:this method must be overridden' )
        return 'get_info:information not available'

    # return rotor tracker 
    def get_tracker( self, coord ):
        eprint('ERROR: get_tracker:this method must be overridden' )

############################################################################

    # general routines 

    # park the antenna
    def park( self ):

        logging.info( 'parking antenna...' )
        eprints( 'parking antenna...' )
        self.move_azel( self.az_park, self.el_park )
        logging.info( 'antenna parked' )
        eprint( 'done.' )
