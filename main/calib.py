'''
@file calib.py
@author Scott L. Williams
@package STaR
@brief Calibration thread.
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
Calibrates the antenna on a different thread so that it can be monitored
by another different thread.
'''

calib_copyright = 'calib.py Copyright (c) 2020 Scott L. Williams ' + \
            'released under GNU GPL V3.0'

#  provide calibration thread for star
from threading import Thread

# calibrate antenna on a different thread so that it can be monitored
# by a different thread
class calib( Thread ):
    def __init__ ( self, rotor ):
        Thread.__init__( self )
        self.running = False
        self.rotor = rotor

    def stop( self ):
        self.running = False

    def run ( self ):
        self.running = True
        self.rotor.calibrate()
        self.rotor.park()
        self.running = False

# end calib.py
